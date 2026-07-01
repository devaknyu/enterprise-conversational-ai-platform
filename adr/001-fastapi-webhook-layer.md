# ADR-001: Use FastAPI as the Dialogflow CX Webhook Receiver and Business Logic Layer

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-30 |
| **Deciders** | Platform Architecture |

---

## Context

Dialogflow CX requires an HTTPS fulfillment webhook endpoint that it calls synchronously during conversation turns. Every time an employee triggers an intent that needs data or action (password reset, ticket creation, policy lookup), Dialogflow POSTs a structured JSON payload to this endpoint and waits for a response — with a 30-second timeout.

We need a Python web framework to host this endpoint. The framework choice affects:
- How we validate and parse the Dialogflow JSON payload
- How we inject and manage service dependencies
- How we write and run tests against the webhook handler
- How the application performs under async workloads (concurrent fulfillment calls, downstream HTTP calls to ServiceNow/AD)
- Developer experience for adding new intent handlers

Options evaluated: **Flask**, **Django**, **FastAPI**, **Google Cloud Functions**.

---

## Decision

**Use FastAPI** (with uvicorn as the ASGI server) as the webhook receiver and the layer where all business logic is orchestrated.

FastAPI is the sole HTTP layer. Dialogflow CX is configured to call `POST /webhook` on our Cloud Run URL. All downstream service calls (Active Directory, ServiceNow, VPN, Gemini) happen synchronously within a single webhook request context.

---

## Rationale

### 1. Async-native execution model

FastAPI runs on ASGI (uvicorn). Every route function is `async def`, and downstream integration calls use `httpx.AsyncClient`. This means:
- A single uvicorn worker can handle multiple concurrent webhook calls without blocking threads
- Downstream HTTP calls to Active Directory and ServiceNow do not block the event loop
- No thread pool overhead, no `asyncio.run()` bridges

Flask and Django are synchronous by default. Achieving true async behavior requires Flask 2.x's async views (still WSGI-based, wraps coroutines in threads) or Django Channels (significant complexity overhead for a webhook-only application).

### 2. Pydantic request/response validation

Dialogflow CX sends a deeply nested JSON payload (`intent_info`, `session_info`, `page_info`, `fulfillment_info`, etc.). FastAPI's native integration with Pydantic v2 means:
- The `WebhookRequest` model is declared once as a Python class
- FastAPI validates the incoming JSON against it automatically
- Malformed payloads return HTTP 422 with structured error detail before any handler code runs
- Type safety is enforced at the model level — no runtime `request.json()["intentInfo"]["displayName"]` dict access that silently returns `None`

With Flask or Django REST Framework, the same validation would require explicit marshmallow schemas or DRF serializers, plus manual wiring.

### 3. Built-in dependency injection

FastAPI's `Depends()` system provides a first-class dependency injection mechanism with no external libraries. Services, database clients, and configuration are declared as dependencies in function signatures:

```python
@router.post("/")
async def handle_webhook(
    dispatcher: IntentDispatcher = Depends(get_intent_dispatcher),
    ...
)
```

This enables:
- **Testability**: `app.dependency_overrides[get_ad_client] = lambda: MockADClient()` replaces dependencies in tests without monkey-patching
- **Singleton management**: `lru_cache` on provider functions ensures one service instance per app lifetime
- **Explicit dependency graph**: the full chain of dependencies is declared, not hidden in global state

Flask and Django have no built-in DI; achieving equivalent testability requires `unittest.mock.patch` at module import level, which is fragile and couples tests to implementation modules.

### 4. Auto-generated OpenAPI documentation

FastAPI generates a `/docs` (Swagger UI) endpoint automatically from Pydantic models and route signatures. During development, this makes it trivial to inspect the exact JSON shape Dialogflow sends and the response shape it expects — without reading Dialogflow documentation every time.

This endpoint is disabled in production (`docs_url=None` when `APP_ENV=production`).

### 5. Right-sized for a webhook application

Django's strength is full-featured web applications: ORM, admin panel, templating, session middleware, form handling. None of these are relevant to a webhook receiver. Django brings substantial framework overhead (startup time, settings complexity) for functionality we do not use.

---

## Alternatives Considered

### Flask

- **Synchronous by default**: Flask views are WSGI-based. Async views in Flask 2.x use a thread executor under the hood, not true async I/O — defeating the performance benefit.
- **No built-in DI**: dependency injection requires manual factory functions or `flask-injector`; testability via `unittest.mock.patch` at module level.
- **No built-in Pydantic**: request parsing is manual `request.json` dict access; validation is an add-on (marshmallow, cerberus, or manual).
- **Verdict**: viable for small APIs, but requires assembling a stack of extensions that FastAPI provides natively.

### Django + Django REST Framework

- **Wrong abstraction level**: Django is designed for database-backed web applications. Its ORM, admin, and templating are unused in a webhook service.
- **Sync by default**: async views exist but are not the idiomatic Django pattern; DRF has limited async support.
- **Startup overhead**: Django's app registry and middleware stack add startup latency (relevant for Cloud Run cold starts).
- **Verbose for APIs**: DRF serializers add boilerplate that Pydantic models eliminate.
- **Verdict**: correct choice for an admin dashboard or content management system; wrong fit for a lean webhook service.

### Google Cloud Functions

- **Cold start latency**: a function that hasn't received traffic recently takes 1–3 seconds to cold-start. Dialogflow's 30-second fulfillment timeout would be consumed. Min instances mitigate this but remove cost advantage.
- **No shared service instances**: each function invocation is independent. Services like `RAGService` (which loads ChromaDB on init) and `LLMService` (which authenticates to Vertex AI on init) would re-initialize on every call if not managed carefully.
- **Fragmented codebase**: splitting one logical application across multiple functions creates deployment and testing complexity with no benefit at this scale.
- **Local development friction**: `functions-framework` replicates the Cloud Functions runtime locally but adds a layer between the code and the test runner.
- **Verdict**: appropriate for truly independent, stateless event handlers. Not appropriate for a service with shared, initialized dependencies.

---

## Consequences

**Positive:**
- Async I/O throughout the application stack — consistent programming model from route to integration client
- Type-safe request/response contracts between Dialogflow and the application layer
- Test isolation via `dependency_overrides` without import-level patching
- OpenAPI spec generated automatically — useful for webhook debugging and integration documentation

**Negative / Trade-offs:**
- Requires uvicorn as the ASGI server (additional deployment dependency vs. gunicorn for Flask/Django)
- FastAPI's DI system requires discipline: all service instantiation must go through provider functions, not inline `SomeService()` calls
- The `create_app()` factory pattern is required for test isolation — the application cannot be instantiated at module import level

**Constraints imposed by this decision:**
- Route functions must contain no business logic — only input extraction, service dispatch, and response mapping
- All business logic lives in `app/services/`
- All DI wiring lives in `app/dependencies.py`
