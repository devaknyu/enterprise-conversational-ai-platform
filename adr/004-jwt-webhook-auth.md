# ADR-004: Use HMAC-SHA256 JWT for Dialogflow CX → FastAPI Webhook Authentication

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-30 |
| **Deciders** | Platform Architecture |

---

## Context

Dialogflow CX makes synchronous HTTPS POST requests to our `/webhook` endpoint for every fulfillment call. This endpoint can execute privileged operations: resetting employee passwords, creating IT tickets, querying internal HR and security policies.

Without authentication on this endpoint, **anyone who discovers the Cloud Run URL can trigger these operations** — no Dialogflow agent required. The URL is not a secret (it appears in Dialogflow CX agent configuration and Cloud Run console).

We need an authentication mechanism that:
- Dialogflow CX can send natively (without custom code in the agent)
- The FastAPI application can validate with minimal overhead
- Does not require a database lookup per request
- Prevents replay attacks (an attacker capturing one valid request cannot reuse it indefinitely)
- Is operationally manageable (secret rotation without service downtime)

Dialogflow CX natively supports three authentication options for webhook requests: **Bearer token**, **Basic Auth**, and **mTLS client certificates**.

Options evaluated: **HMAC-SHA256 JWT (HS256)**, **HTTP Basic Auth**, **mTLS**, **OAuth2 Client Credentials**, **Plain API key**.

---

## Decision

**Use HMAC-SHA256 JWT (HS256) with a shared secret**, delivered as a Bearer token in the `Authorization` header.

- Dialogflow CX webhook configuration: set the "Bearer token" field to a long-lived signed JWT
- FastAPI `WebhookAuthMiddleware`: validates the JWT signature and `exp` claim on every `/webhook` request
- Secret: `JWT_SECRET_KEY` (minimum 32 characters), stored in Secret Manager in production, `.env` in development
- Token expiry: configurable via `JWT_EXPIRY_MINUTES` (default 60 minutes); tokens are regenerated via `scripts/generate_jwt.py`

---

## Rationale

### 1. Dialogflow CX native bearer token support

Dialogflow CX webhook configuration has an explicit "Authentication" section with a "Bearer token" field. When configured, Dialogflow includes `Authorization: Bearer <token>` in every fulfillment HTTP request automatically — no changes to the Dialogflow agent flows, no custom Dialogflow code, no fulfillment-side token injection logic.

This is the zero-friction path. The authentication contract is: Dialogflow knows the token (configured once in the console), FastAPI validates it on every request.

### 2. Stateless validation — no database lookup

JWT validation is a pure cryptographic operation:
1. Base64-decode the header and payload
2. Recompute the HMAC-SHA256 signature using `JWT_SECRET_KEY`
3. Compare with the signature in the token
4. Check the `exp` claim against the current time

No database, no cache, no network call. The validation adds approximately 0.5–1ms to each webhook request — negligible against the 100–500ms downstream service call latency.

HTTP Basic Auth validation is similarly stateless if the credentials are checked against a constant. However, Basic Auth provides no expiry mechanism (see point 3).

### 3. Replay attack protection via `exp` claim

JWT includes a standard `exp` (expiration time) claim. A token with `exp` set 60 minutes from issuance will be rejected by `WebhookAuthMiddleware` after those 60 minutes, even if the token is cryptographically valid.

This bounds the window of vulnerability if a JWT is intercepted or leaked: an attacker who captures a valid token can only replay it for at most `JWT_EXPIRY_MINUTES` minutes.

A plain API key or HTTP Basic Auth credentials have no expiry. If compromised, they are valid indefinitely until manually rotated.

### 4. Standard, well-understood security primitive

HS256 JWT is a well-audited standard (RFC 7519). `python-jose` implements it correctly with validation of signature, expiry, and algorithm. There is no custom cryptographic code.

The security properties are well-documented and easy to explain in a compliance review: "Dialogflow sends a signed token; we verify the signature and check it hasn't expired."

---

## Authentication Flow

```
[Dialogflow CX Configuration]
  → Bearer token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    (pre-generated, stored in Dialogflow webhook settings)

[Fulfillment Call]
  Dialogflow CX → POST /webhook
  Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

[WebhookAuthMiddleware]
  1. Extract token from Authorization header → 401 if missing
  2. jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
     → raises JWTError if signature invalid → 401
     → raises ExpiredSignatureError if exp in past → 401
  3. Request proceeds to route handler

[Token Generation — development]
  python scripts/generate_jwt.py
  → prints a signed JWT with exp = now + JWT_EXPIRY_MINUTES
  → developer pastes into Dialogflow CX webhook settings
```

---

## Alternatives Considered

### HTTP Basic Auth

**How it works:** Dialogflow sends `Authorization: Basic base64(username:password)` in every request. FastAPI middleware decodes and compares against configured credentials.

**Why it was not chosen:**
- No expiry: credentials are valid indefinitely until manually rotated; rotation requires updating both the Dialogflow webhook config and the application secret simultaneously
- Weaker by convention: base64 is encoding, not encryption; Basic Auth credentials are trivially reversible if the header is observed
- Slightly higher phishing/brute-force surface compared to a long random JWT
- **Verdict**: acceptable for low-sensitivity webhook receivers; insufficient for an endpoint that can trigger password resets

### mTLS (Mutual TLS)

**How it works:** The client (Dialogflow) presents a client certificate. The server (FastAPI) validates the certificate against a trusted CA. Provides strong authentication without secrets.

**Why it was not chosen:**
- **Dialogflow CX client certificate support is limited**: Dialogflow CX supports presenting a client certificate for webhook calls, but the configuration is non-trivial and documentation is sparse. Operational issues are hard to debug.
- **Certificate lifecycle**: client certificates have expiry dates and must be rotated before expiry. Rotation involves generating a new certificate, updating the Dialogflow webhook config, and ensuring no gap in coverage.
- **Local development**: mTLS requires generating a local CA, issuing a client cert, configuring uvicorn to request it, and configuring the test client to present it. This adds significant development friction.
- **Verdict**: the most technically robust option for production enterprise deployments at scale. Should be reconsidered if the security posture requirement escalates (e.g., PCI-DSS, HIPAA-regulated environment). For this portfolio project, the operational complexity is not justified.

### OAuth2 Client Credentials Flow

**How it works:** Dialogflow obtains a short-lived access token from an authorization server (Google Cloud IAM, Auth0, etc.) before each webhook call, then presents it as a Bearer token.

**Why it was not chosen:**
- **Overkill for service-to-service**: OAuth2 client credentials is designed for scenarios where a client authenticates to a third-party authorization server it doesn't own. Here, Dialogflow and FastAPI are both our infrastructure — we control both sides.
- **Added dependency**: requires an authorization server (or Google Cloud IAM OAuth2 endpoint) that must be reachable every time Dialogflow needs to refresh a token
- **Complexity without benefit**: the security properties of client credentials vs. a well-managed JWT shared secret are similar for this use case
- **Verdict**: appropriate if the webhook endpoint is exposed to multiple external clients that need independent credentials. Not warranted for a single Dialogflow agent caller.

### Plain API Key (static string, no JWT structure)

**How it works:** A random string (e.g., `sk-abc123...`) is stored in both Dialogflow and the application. The middleware compares the header value against the expected key using `secrets.compare_digest()`.

**Why it was not chosen:**
- No expiry: an API key is valid until manually rotated
- No replay protection: a captured key is valid indefinitely
- Harder to audit: a JWT payload can include `iss` (issuer), `sub` (subject), and custom claims that make audit logs more informative; a plain key carries no structured metadata
- **Verdict**: the simplest possible solution, but the additional security properties of JWT (`exp`, structured claims) cost nothing to add and provide meaningful improvements

---

## Consequences

**Positive:**
- Zero-friction Dialogflow configuration: paste a token into the webhook settings, done
- Stateless validation with no infrastructure dependency
- Replay attack window bounded by token expiry
- Easy to rotate: generate a new JWT, update Dialogflow config, no application redeployment required

**Negative / Trade-offs:**
- Token lifetime creates a rotation cadence: tokens must be regenerated and updated in Dialogflow CX before expiry. A missed rotation causes all webhook calls to return 401 until the token is refreshed. *Mitigation: generate tokens with 1-year expiry in production and use a calendar reminder for rotation; or generate short-lived tokens and automate rotation via a scheduled job.*
- JWT theft is possible if HTTPS is not enforced. *Mitigation: Cloud Run enforces HTTPS on all traffic — HTTP requests are redirected to HTTPS automatically.*
- The `JWT_SECRET_KEY` is a symmetric secret shared between Dialogflow (which holds the token) and FastAPI (which holds the signing key). If the secret leaks, all tokens signed with it are compromised. *Mitigation: store `JWT_SECRET_KEY` in Secret Manager; rotate immediately if exposure is suspected.*

**Operational requirements:**
- `JWT_SECRET_KEY` in Secret Manager (production); `.env` (development)
- Token generation: `python scripts/generate_jwt.py` outputs a valid token for pasting into Dialogflow
- Dialogflow CX webhook configuration: Authentication → Bearer token → paste generated JWT
- Monitor for sustained `auth_error` log events in Cloud Logging — indicates either token expiry or unauthorized scanning
