# Architecture: Enterprise IT Support Assistant

> Version 1.0 — Phase 1 Architecture Design
> Last updated: 2026-06-30

---

## 1. Executive Summary

The Enterprise IT Support Assistant is a cloud-native Conversational AI platform built for Fortune 500 employees. It handles common IT support requests — password resets, VPN troubleshooting, software installation guidance, IT ticket management, and policy questions — via natural language, available through both chat and voice interfaces.

The platform is architected for enterprise correctness, not prototype simplicity. Every design decision prioritizes: testability (dependency injection everywhere), auditability (structured logging into Cloud Logging), data residency (all inference stays on GCP), and operational replaceability (mock integrations swappable for real APIs with zero code changes).

The platform processes requests as follows: an employee speaks or types a request → Dialogflow CX extracts intent and entities → a FastAPI webhook handler executes business logic → the response flows back through Dialogflow to the employee. No business logic lives in Dialogflow. No data persists beyond what ServiceNow or Active Directory own.

---

## 2. System Context

```
Fortune 500 Employee
        │
        │  (Chat / Voice)
        ▼
  ┌─────────────────┐
  │  Dialogflow CX  │  ← Conversation state, intent classification, entity extraction
  │  (Google Cloud) │     Does NOT hold business logic or make data decisions
  └────────┬────────┘
           │  HTTPS POST /webhook
           │  Bearer JWT
           ▼
  ┌─────────────────────────────────────────────────────┐
  │              FastAPI Application                     │
  │  (Google Cloud Run — containerized, auto-scaling)   │
  │                                                      │
  │  ┌──────────────┐   ┌──────────────────────────┐   │
  │  │ Auth         │   │ Intent Dispatcher        │   │
  │  │ Middleware   │   │ (routes to handlers)     │   │
  │  └──────────────┘   └──────────────────────────┘   │
  │                                                      │
  │  ┌──────────────────────────────────────────────┐   │
  │  │            Business Services                 │   │
  │  │  Password │ Ticket │ VPN │ Escalation │ Session │
  │  └──────────────────────────────────────────────┘   │
  │                                                      │
  │  ┌──────────────────────────────────────────────┐   │
  │  │            Platform Services                 │   │
  │  │     LLMService (Gemini)  │  RAGService       │   │
  │  └──────────────────────────────────────────────┘   │
  └──────────────────────┬──────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ServiceNow│  │Active Dir│  │VPN Gateway│
    │  (Mock)  │  │  (Mock)  │  │  (Mock)  │
    └──────────┘  └──────────┘  └──────────┘
           │
           ▼
    ┌──────────────────┐
    │  Vertex AI       │
    │  Gemini 1.5 Pro  │
    │  text-embedding  │
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │  ChromaDB        │
    │  (embedded,      │
    │   local persist) │
    └──────────────────┘
```

---

## 3. Component Responsibilities

### 3.1 Dialogflow CX

**Role:** Conversation state machine and NLU layer.

Dialogflow CX owns:
- Intent classification (what does the employee want?)
- Entity extraction (user_email, ticket_id, issue_description, etc.)
- Flow control (multi-turn conversation state, page transitions)
- Voice channel integration (DTMF, speech synthesis)
- Session parameters (passing extracted values to the webhook)

Dialogflow CX does **not** own:
- Business logic of any kind
- Data persistence
- Decision-making about what action to take (that belongs to the handler)
- Retry logic for failed operations

Every Dialogflow page that requires data or action has exactly one fulfillment webhook call configured. Dialogflow is the front door; FastAPI is where work happens.

### 3.2 FastAPI Webhook Layer (`app/api/`)

**Role:** HTTPS endpoint, request parsing, authentication enforcement, routing.

The `/webhook` endpoint (`app/api/routes/webhook.py`) is the sole entry point for Dialogflow fulfillment calls. It:
1. Receives the raw Dialogflow `WebhookRequest` JSON payload
2. Validates it against the Pydantic `WebhookRequest` model (automatic — rejects malformed payloads with 422)
3. Passes it to the `IntentDispatcher`
4. Returns the `WebhookResponse` Pydantic model (serialized to JSON matching Dialogflow's expected format)

The route function contains zero business logic. It maps HTTP → service call → HTTP response. Exception types from `core/exceptions.py` are caught at the route level and converted to appropriate fallback `WebhookResponse` messages (never raw HTTP 500 back to Dialogflow).

### 3.3 Auth Middleware (`app/api/middleware/auth.py`)

**Role:** JWT validation on every inbound webhook call.

`WebhookAuthMiddleware` runs before every request to `/webhook`. It:
1. Extracts the `Authorization: Bearer <token>` header
2. Decodes and validates the JWT against `JWT_SECRET_KEY` using HS256
3. Checks `exp` claim (rejects expired tokens)
4. Rejects with HTTP 401 if any validation fails

Validation is stateless — no database lookup, no cache. The cryptographic check is the only gate. This middleware is not applied to `/health` or `/ready` endpoints.

See [ADR-004](../adr/004-jwt-webhook-auth.md) for the decision rationale.

### 3.4 Intent Dispatcher (`app/webhook/dispatcher.py`)

**Role:** Map intent display name to the registered handler.

The `IntentDispatcher` maintains a registry of `intent_name → handler` mappings. On each request:
1. Extracts `intent_info.display_name` from the webhook request
2. Looks up the registered handler
3. Calls `handler.handle(request)` and returns the response

If no handler is found, raises `IntentNotFoundError` (caught by the route, returns a graceful fallback message to the employee). This is a single-responsibility component — it does nothing but route.

Handler registry example:
```
"it.password.reset"     → PasswordHandler
"it.ticket.create"      → TicketHandler
"it.ticket.status"      → TicketHandler
"it.vpn.troubleshoot"   → VPNHandler
"it.policy.query"       → RAGHandler
"it.escalate"           → EscalationHandler
```

### 3.5 Webhook Handlers (`app/webhook/handlers/`)

**Role:** Translate Dialogflow request parameters into service calls and format the response.

Each handler:
1. Extracts required parameters from `session_info.parameters` (raises `MissingParameterError` if absent)
2. Calls the appropriate business service method
3. Passes the result to `ResponseBuilder` to construct the `WebhookResponse`

Handlers know about Dialogflow's data shape and the service interface. They know nothing about HTTP, authentication, or database access.

### 3.6 Business Services (`app/services/business/`)

**Role:** Domain logic for each IT support capability.

Each service inherits from `BaseService` and receives all dependencies via constructor injection. Services know nothing about HTTP, Dialogflow, or response formatting.

| Service | Responsibility | Integration |
|---|---|---|
| `PasswordService` | Validate user, initiate AD password reset, record action | `ActiveDirectoryClient` |
| `TicketService` | Create/query ServiceNow incidents, apply priority rules | `ServiceNowClient` |
| `VPNService` | Run diagnostic checks, apply remediation steps | `VPNClient` |
| `EscalationService` | Transfer conversation to human agent, create escalation record | `ServiceNowClient` |
| `SessionService` | Track per-session state and action history | In-memory (Phase 1); Redis in production |

Services raise only typed exceptions from `core/exceptions.py`. They never raise raw `Exception`.

### 3.7 Platform Services (`app/services/platform/`)

**Role:** Infrastructure-level capabilities shared across business services.

**`LLMService`** — the sole Gemini caller in the codebase. Accepts a structured prompt (system instructions + RAG context + user query), calls Vertex AI, returns the generated text. Business services and handlers never call Gemini directly.

**`RAGService`** — ChromaDB retrieval. Accepts a natural language query, generates an embedding via Vertex AI `text-embedding-004`, performs a similarity search against the IT knowledge base collection, returns the top-k chunks with metadata. Always called before `LLMService` for policy questions.

See [ADR-002](../adr/002-chromadb-vs-faiss.md) and [ADR-003](../adr/003-gemini-vertex-sdk.md).

### 3.8 Integration Layer (`app/integrations/`)

**Role:** Adapter pattern between business services and external APIs.

Every external system has three files:
- `base.py` — abstract interface (the contract business services depend on)
- `client.py` — real implementation using `httpx` with `tenacity` retry logic
- `mock.py` — mock implementation with realistic latency (100–300ms) and configurable error rate (default 5%)

The switch between real and mock is controlled entirely by `USE_MOCK_INTEGRATIONS=true/false` in the environment. Zero code changes required. The DI container in `app/dependencies.py` resolves the correct implementation at startup.

### 3.9 Response Builder (`app/webhook/response_builder.py`)

**Role:** Construct Dialogflow-formatted `WebhookResponse` objects from service results.

Encapsulates all knowledge of the Dialogflow webhook response format. Handlers call `ResponseBuilder.build(...)` with domain data; they never hand-construct response JSON. This makes handler code readable and keeps Dialogflow format changes isolated to one place.

---

## 4. Request Lifecycle (End-to-End)

This trace follows a password reset request through every layer:

```
1. Employee types: "I need to reset my password"

2. Dialogflow CX:
   - Matches intent: "it.password.reset"
   - Extracts entity: user_email = "john.doe@acme.com" (from session or entity extraction)
   - Triggers fulfillment: POST https://<cloud-run-url>/webhook
     Headers: Authorization: Bearer <signed-jwt>
     Body: WebhookRequest JSON with intent_info, session_info, parameters

3. FastAPI receives request:
   - RequestLoggingMiddleware: logs request_id, intent, session_id
   - WebhookAuthMiddleware: validates JWT signature and exp claim → 401 if invalid
   - Route: parses body into WebhookRequest Pydantic model → 422 if malformed

4. IntentDispatcher:
   - Reads intent_info.display_name = "it.password.reset"
   - Looks up PasswordHandler in registry
   - Calls PasswordHandler.handle(webhook_request)

5. PasswordHandler:
   - Extracts user_email from session_info.parameters
   - Raises MissingParameterError if absent
   - Calls PasswordService.initiate_reset(user_id="john.doe@acme.com", session_id="...")

6. PasswordService:
   - Calls SessionService.record_action(session_id, action="password_reset", metadata={...})
   - Calls ADClient.reset_password("john.doe@acme.com")
     → Mock: waits 100–300ms, returns PasswordResetResult(success=True, delivery="email")
     → Real: POST to Active Directory API with retry on TransportError/TimeoutException
   - Returns PasswordResetResult

7. PasswordHandler:
   - Passes result to ResponseBuilder.build_password_reset_response(result)
   - ResponseBuilder returns WebhookResponse with fulfillment message

8. FastAPI:
   - Serializes WebhookResponse to JSON
   - Returns HTTP 200

9. Dialogflow CX:
   - Receives WebhookResponse
   - Reads fulfillment message text
   - Plays/displays to employee: "Your password reset email has been sent to your registered address.
     You should receive it within 5 minutes. Reference: AD-RESET-84729301"

Total latency budget: ~300ms (mock) / ~500ms (real AD with network)
```

---

## 5. Key Architectural Constraints

These are non-negotiable invariants in the codebase. Violations are considered bugs.

- **Gemini is called only from `LLMService`** — never from routes, handlers, or business services directly. This ensures token usage is tracked in one place and prompt structure is centralized.

- **RAG retrieval always precedes Gemini for policy questions** — `RAGHandler` calls `RAGService.retrieve()` before `LLMService.generate()`. Grounding is not optional.

- **No business logic in route functions** — routes call services, return responses. The longest a route function should be is ~20 lines including error handling.

- **Mocks injected via DI, not hardcoded** — `USE_MOCK_INTEGRATIONS` controls which implementation the DI container provides. No `if USE_MOCK` conditionals inside service or handler code.

- **All external calls use httpx with tenacity retry** — no bare `requests` calls, no retry logic duplicated in individual clients.

- **No credentials in source code** — JWT secrets, API keys, service account paths all come from environment variables via `pydantic-settings`.

- **Structured logging everywhere** — every `logger.info/warning/error` call includes key=value context fields. No f-string messages.

---

## 6. Architecture Decision Records

| ADR | Decision | File |
|---|---|---|
| ADR-001 | Use FastAPI as the Dialogflow webhook receiver and business logic layer | [adr/001-fastapi-webhook-layer.md](../adr/001-fastapi-webhook-layer.md) |
| ADR-002 | Use ChromaDB as the vector store for RAG (vs FAISS, Pinecone, Weaviate) | [adr/002-chromadb-vs-faiss.md](../adr/002-chromadb-vs-faiss.md) |
| ADR-003 | Use Gemini 1.5 Pro via Vertex AI SDK for LLM inference | [adr/003-gemini-vertex-sdk.md](../adr/003-gemini-vertex-sdk.md) |
| ADR-004 | Use HMAC-SHA256 JWT for Dialogflow → FastAPI webhook authentication | [adr/004-jwt-webhook-auth.md](../adr/004-jwt-webhook-auth.md) |

---

## 7. Deployment Architecture

The platform runs as a single containerized FastAPI application on Google Cloud Run.

```
Developer → Docker build → Artifact Registry → Cloud Run (auto-deploy)
                                                      │
                                                      ├── Vertex AI (Gemini, Embeddings)
                                                      ├── Cloud Logging (structlog output)
                                                      ├── Secret Manager (JWT_SECRET_KEY, etc.)
                                                      └── (Future) Cloud SQL / Redis
```

Key Cloud Run properties:
- **HTTPS-only**: Cloud Run enforces TLS termination — JWT tokens are never transmitted in plaintext
- **Zero-to-N scaling**: Each instance is stateless (session data is in-memory per-instance in Phase 1)
- **IAM-attached service account**: No `GOOGLE_APPLICATION_CREDENTIALS` file in production — Vertex AI auth is transparent
- **Min instances = 1** in production to avoid cold start latency on fulfillment calls

For detailed deployment steps, environment variable configuration, and Cloud Run service setup, see `docs/deployment.md`.

---

## 8. Security Architecture

| Concern | Control |
|---|---|
| Unauthorized webhook calls | JWT Bearer token validated by `WebhookAuthMiddleware` on every `/webhook` request |
| Token replay | `exp` claim in JWT; default 60-minute expiry |
| Credential exposure | All secrets in environment variables; production secrets in Secret Manager |
| Data in transit | HTTPS enforced by Cloud Run; no plaintext communication |
| Prompt injection | User input passed to Gemini only via structured prompt template in `LLMService`; raw employee text never interpolated without sanitization |
| PII in logs | Structured log fields explicitly chosen per event — no wildcard request body logging |

---

## 9. Observability Architecture

All application logging uses `structlog` configured in `app/core/logging.py`:

- **Development**: Pretty-printed console output for readability
- **Production**: JSON output, ingested by Cloud Logging via stdout collection (Cloud Run default)

Every log event includes structured context:
```json
{
  "event": "password_reset_initiated",
  "service": "PasswordService",
  "user_id": "john.doe@acme.com",
  "session_id": "projects/.../sessions/sess-001",
  "request_id": "req-abc123",
  "timestamp": "2026-06-30T10:15:00Z",
  "level": "info"
}
```

**Recommended Cloud Logging alert candidates:**

| Log event | Suggested alert |
|---|---|
| `intent_not_found` | High rate → Dialogflow flow misconfiguration |
| `password_reset_failed` | Any occurrence in production |
| `mock_transient_error_injected` | Should never appear in production |
| `http_error` with status 5xx | Integration downstream issue |
| `auth_error` | Sustained rate → potential unauthorized scanning |

---

## 10. Known Tradeoffs and Limitations

| Tradeoff | Detail | Mitigation Path |
|---|---|---|
| ChromaDB not suited for large corpora | HNSW index degrades beyond ~100K vectors | Migrate to Pinecone or Vertex AI Vector Search at scale |
| Session state is in-memory per-instance | Cloud Run scales to multiple instances; sessions may not persist across instances | Replace `SessionService` storage with Redis (Cloud Memorystore) in Phase 3b |
| Mock integrations only | No real ServiceNow, AD, or VPN in Phase 1 | DI pattern makes swap zero-code-change; real clients implemented in Phase 3c |
| HS256 JWT replay window | A stolen JWT can be replayed until expiry (default 60 min) | Rotate `JWT_SECRET_KEY` periodically; consider short-lived tokens (5 min) in production |
| Single webhook endpoint | All intents funnel through one `/webhook` route | IntentDispatcher provides clean routing; extend with versioned routes if Dialogflow agent is versioned |
| Gemini model version pinned | `gemini-1.5-pro` specified; breaking changes on model upgrade | `VERTEX_AI_MODEL` env var allows hot-swap without redeployment |
