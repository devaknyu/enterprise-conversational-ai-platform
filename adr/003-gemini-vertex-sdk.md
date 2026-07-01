# ADR-003: Use Gemini 1.5 Pro via Vertex AI SDK for LLM Inference

| Field | Value |
|---|---|
| **Status** | Accepted (amended 2026-06-30: dev/prod backend split added) |
| **Date** | 2026-06-30 |
| **Deciders** | Platform Architecture |

---

## Context

The platform needs a large language model for two purposes:
1. **Grounded policy answer generation**: given RAG-retrieved chunks from the IT knowledge base, generate a natural language answer to the employee's question
2. **Fallback response generation**: for queries that don't match a specific intent but require a conversational response

The LLM must satisfy the following enterprise requirements:
- **Data residency**: employee queries and retrieved document context must not leave the customer's cloud environment
- **Enterprise auth**: credentials must be manageable via IAM, not individual API keys
- **Auditability**: every inference call must be auditable via cloud-native audit logging
- **Reliability**: the model must have production SLAs appropriate for a Fortune 500 deployment
- **Context capacity**: RAG retrieval may return several chunks of policy text; the model must handle 4K–32K token contexts comfortably

Options evaluated: **Gemini 1.5 Pro via Vertex AI**, **Gemini via AI Studio (Direct API)**, **OpenAI GPT-4 (via OpenAI API)**, **Anthropic Claude (via Anthropic API)**.

---

## Decision

**Use Gemini 1.5 Pro via the Vertex AI Python SDK** (`google-cloud-aiplatform` / `vertexai`).

The model is called exclusively through `LLMService` (`app/services/platform/llm_service.py`). No other file in the codebase imports or instantiates any Vertex AI or Gemini client. The model name is configurable via `VERTEX_AI_MODEL` environment variable (`gemini-1.5-pro` default).

---

## Rationale

### 1. Data residency within Google Cloud

This is the decisive factor for an enterprise deployment. Employee IT requests often contain PII (user IDs, email addresses, descriptions of personal device issues). Policy documents may contain internal security procedures.

When calling Gemini via Vertex AI, all inference occurs within the customer's Google Cloud project. The data never leaves the GCP boundary to a third-party model provider. This satisfies:
- Enterprise data governance policies
- GDPR data processing agreements (data stays in the declared region)
- Internal security review requirements that prohibit sending corporate data to external SaaS APIs

OpenAI GPT-4 and Anthropic Claude (via their direct APIs) both send request data to external APIs outside the customer's cloud control boundary. This alone disqualifies them for this deployment scenario.

*Note: Both OpenAI and Anthropic models are available via Vertex AI Model Garden, which would satisfy the data residency requirement. However, Gemini is the native GCP LLM, better integrated with Vertex AI infrastructure, and avoids additional licensing complexity.*

### 2. IAM-based authentication — no API keys in production

Vertex AI uses Google Cloud's IAM for authentication. In Cloud Run:
- The service account attached to the Cloud Run service is granted `roles/aiplatform.user`
- The `vertexai` SDK uses Application Default Credentials automatically
- No `GEMINI_API_KEY` environment variable exists in production

This eliminates an entire class of credential management problems:
- No API key rotation schedule
- No risk of API key leakage in environment variables or logs
- No need for Secret Manager to store a model API key (JWT secrets and integration credentials are still in Secret Manager)
- IAM policies control exactly which Cloud Run services can call which Vertex AI resources

AI Studio API keys are long-lived credentials stored in environment variables — they require manual rotation, and accidental exposure (e.g., logging a full request) is a security incident.

### 3. Vertex AI audit logging

Every `GenerateContent` call to Vertex AI generates a Cloud Audit Log entry that records:
- Which service account made the call
- Which model was invoked
- Timestamp
- Request/response metadata (not content by default, but configurable)

This satisfies enterprise compliance requirements for AI usage tracking. There is no equivalent native audit trail for direct OpenAI or Anthropic API calls without custom logging middleware.

### 4. 1M-token context window (Gemini 1.5 Pro)

Gemini 1.5 Pro's 1-million-token context window ensures RAG-retrieved chunks never need to be truncated due to context length limits. For a knowledge base of IT policy documents, retrieval may return 5–10 chunks of 500 tokens each (~5000 tokens total). This fits comfortably within any modern LLM context window, but the generous limit provides headroom if the RAG strategy evolves to retrieve more context.

### 5. GCP-native networking — no egress cost

Calls from Cloud Run to Vertex AI travel over Google's internal network:
- No external egress bandwidth cost
- Lower and more predictable latency compared to external API calls over the public internet
- Consistent with the overall GCP-committed architecture (Dialogflow CX, Cloud Run, Vertex AI, Cloud Logging all on GCP)

One IAM model, one billing account, one support contact.

---

## Integration Constraint

**Gemini is called only from `LLMService`.** This is enforced by convention and code review, not by technical enforcement. The rationale:

- Token usage tracking is centralized in one place
- Prompt structure (system instructions, RAG context injection, user query formatting) is defined once
- Safety filter configuration is managed in one place
- If the model changes (e.g., Gemini 2.0 replaces 1.5 Pro), one file changes

If a business service or handler were to call Gemini directly:
- Prompt construction would be scattered across the codebase
- Token usage would be invisible
- Testing would require mocking Vertex AI in multiple places instead of one

---

## Alternatives Considered

### Gemini via AI Studio (Direct API)

**Why it was considered:** Simpler setup — a single `GEMINI_API_KEY` environment variable, no GCP project configuration.

**Why it was not chosen:**
- Key-based auth: API keys are long-lived credentials requiring manual rotation
- No enterprise SLAs for AI Studio usage
- Data is sent to Google's AI Studio infrastructure, which may differ from Vertex AI's enterprise data handling
- No Cloud Audit Logs integration
- **Verdict**: appropriate for prototyping and personal projects; not for a production enterprise deployment.

### OpenAI GPT-4 (via OpenAI API)

**Why it was considered:** GPT-4 is a strong model with broad ecosystem support. OpenAI's enterprise tier provides data processing agreements.

**Why it was not chosen:**
- Data leaves GCP to OpenAI's infrastructure (even with DPA, the data residency model differs from GCP-native)
- API key management in environment variables
- Additional vendor: introduces a second billing relationship, API key rotation process, and monitoring surface
- Does not benefit from GCP-native IAM, audit logging, or internal networking
- **Verdict**: a valid production choice if the customer is not GCP-committed or if GPT-4 is contractually required.

### Anthropic Claude (via Anthropic API / Vertex AI Model Garden)

**Why it was considered:** Claude is a capable model with strong instruction-following. Available on Vertex AI Model Garden.

**Why it was not chosen:**
- Via direct Anthropic API: same data residency concerns as OpenAI
- Via Vertex AI Model Garden: technically satisfies data residency, but Gemini is the native GCP model — better integrated, lower latency, simpler licensing
- No additional benefit over Gemini 1.5 Pro for this use case (IT support policy Q&A)
- **Verdict**: appropriate if Claude's specific capabilities (e.g., Constitutional AI, specific safety profiles) are required by the customer.

---

## Development Implementation (Cost-Free)

Vertex AI Gemini is paid. To keep development cost at $0, `LLMService` supports a pluggable backend architecture:

| Env var | Value | Backend | Cost |
|---|---|---|---|
| `LLM_BACKEND` | `gemini_api` | `google-generativeai` package + AI Studio API key | **$0** — free tier |
| `LLM_BACKEND` | `vertex_ai` | `vertexai` package + GCP IAM auth | Paid per token |

**Default is `gemini_api` (free).** Vertex AI is explicitly opt-in via env var.

### Free tier details (as of 2026)
- Model: `gemini-2.0-flash` (capable, fast, same Gemini family)
- Limits: 15 RPM, 1500 requests/day, 1M tokens/day — more than sufficient for development and portfolio demos
- Auth: free API key from [aistudio.google.com](https://aistudio.google.com) — no billing account required
- Package: `pip install google-generativeai`

### Code architecture (implemented in Phase 5)

```
app/services/platform/
├── llm_service.py                  # LLMService — calls self.backend.generate(prompt)
└── llm_backends/
    ├── base.py                     # BaseLLMBackend: generate(prompt: str) -> str
    ├── gemini_api.py               # Uses google-generativeai (dev/free)
    └── vertex_ai.py                # Uses vertexai SDK (prod/paid)
```

The DI container reads `LLM_BACKEND` and injects the correct backend into `LLMService`. No conditional logic inside `LLMService` itself — it only calls `self.backend.generate(prompt)`.

### Production rationale still applies

The production reasons for Vertex AI (data residency, IAM auth, Cloud Audit Logs) are unchanged and documented above. The dev/prod split does not weaken the production architecture — it just avoids charging for development work.

---

## Consequences

**Positive:**
- Zero credential files in production containers
- Every inference call auditable via Cloud Audit Logs
- No data residency concerns for enterprise customers
- Model upgrades handled by changing one environment variable
- **Development is $0** — no billing account, no GCP project, no service account needed to run locally

**Negative / Trade-offs:**
- Two packages to maintain (`google-generativeai` for dev, `google-cloud-aiplatform` for prod), though both install without conflict
- `gemini-2.0-flash` (dev) differs from `gemini-1.5-pro` (prod) — response quality may differ slightly; test prompts against the prod model before production deployment
- Vertex AI has regional availability constraints — `GOOGLE_CLOUD_REGION` must match a region where Gemini 1.5 Pro is available (`us-central1` is the safe default)
- Vertex AI quotas (requests per minute, tokens per minute) are project-level — must be monitored in production via Cloud Monitoring

**Operational requirements (production):**
- Service account: `roles/aiplatform.user` on the GCP project
- Cloud Run: service account attached via `--service-account` at deploy time; no credentials file
- Quota monitoring: set up Cloud Monitoring alerts on `aiplatform.googleapis.com/prediction/online/request_count` and error rates

**Operational requirements (development):**
- Generate a free API key at aistudio.google.com
- Set `GEMINI_API_KEY=<your-key>` in `.env`
- Set `LLM_BACKEND=gemini_api` (this is the default)
- No GCP project, no service account, no billing
