# Enterprise IT Support Assistant

An enterprise-grade Conversational AI platform for IT support. Built to demonstrate
production-quality Conversational AI engineering: multi-service backend, LLM orchestration,
RAG, enterprise integrations, JWT authentication, dependency injection, and cloud-native deployment.

**Tech Stack:** Dialogflow CX · FastAPI · Gemini (free dev tier / Vertex AI prod) · ChromaDB · Python 3.11 · Cloud Run

---

## What It Does

Employees chat via Dialogflow CX to:
- Reset their Active Directory password
- Create and track IT support tickets (ServiceNow)
- Troubleshoot VPN connectivity issues
- Ask questions about IT policies (answered via RAG + Gemini)
- Escalate to a human agent

---

## Architecture

```
Employee → Dialogflow CX → FastAPI /webhook → IntentDispatcher
                                                    ↓
                                          Business Services
                                     (Password/Ticket/VPN/Session)
                                                    ↓
                                         Platform Services
                                       (LLMService/RAGService)
                                                    ↓
                                      Integrations (Mock in Dev)
                                    (Active Directory/ServiceNow/VPN)
```

See [docs/architecture.md](docs/architecture.md) for the full narrative.
See [adr/](adr/) for Architecture Decision Records explaining every major choice.

---

## Local Development Setup (100% Free)

### Prerequisites

- Python 3.11+
- Git

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd enterprise-conversational-ai-platform
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set the required values:

```bash
JWT_SECRET_KEY=any-random-string-at-least-32-characters
WEBHOOK_SHARED_SECRET=any-random-string-16-chars-min
GEMINI_API_KEY=your-free-key-from-aistudio.google.com
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) — no billing account required.
The defaults (`LLM_BACKEND=gemini_api`, `EMBEDDING_BACKEND=local`) use the free tier automatically.

### 3. Ingest the knowledge base

```bash
python scripts/ingest_knowledge_base.py
```

This runs once. Re-run after adding documents to `knowledge_base/documents/`.

### 4. Run the application

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at http://localhost:8000. Interactive docs at http://localhost:8000/docs.

### 5. Generate a test JWT and send a test request

```bash
python scripts/generate_jwt.py
```

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <generated-token>" \
  -d '{
    "intentInfo": {"displayName": "it.password.reset"},
    "sessionInfo": {
      "session": "projects/test/locations/us-central1/agents/test/sessions/sess-001",
      "parameters": {"user_email": "john.doe@acme.com"}
    }
  }'
```

---

## Running Tests

```bash
pytest                           # All tests
pytest -m unit                   # Unit tests only
pytest -m integration            # Integration tests only
pytest --cov=app --cov-report=html  # With coverage report
```

No GCP credentials are needed to run the test suite.

---

## Docker (Local)

```bash
# Development (hot reload)
docker-compose -f docker-compose.dev.yml up

# Production-equivalent
docker-compose up
```

---

## Production Deployment

See [docs/deployment.md](docs/deployment.md) for Cloud Run deployment steps.

In production:
- `LLM_BACKEND=vertex_ai` — Gemini 1.5 Pro via Vertex AI (IAM auth, data residency)
- `EMBEDDING_BACKEND=vertex_ai` — text-embedding-004
- `USE_MOCK_INTEGRATIONS=false` — real ServiceNow and Active Directory

---

## Project Structure

```
app/                        FastAPI application
  api/routes/               HTTP endpoints (webhook, health, admin)
  api/middleware/           JWT auth and request logging middleware
  core/                     Exceptions, logging config, JWT utilities
  models/                   Pydantic models (Dialogflow, tickets, users)
  services/business/        Domain services (password, ticket, VPN, session)
  services/platform/        LLM and RAG services with pluggable backends
  integrations/             External API clients (mock + real)
  webhook/                  Intent dispatcher, handlers, response builder
adr/                        Architecture Decision Records
docs/                       Architecture narrative, deployment guide
knowledge_base/documents/   IT policy documents (RAG source)
scripts/                    Dev helper scripts
tests/                      Unit and integration tests
```

---

## Architecture Decisions

| Decision | ADR |
|---|---|
| Why FastAPI over Flask/Django? | [ADR-001](adr/001-fastapi-webhook-layer.md) |
| Why ChromaDB over FAISS/Pinecone? | [ADR-002](adr/002-chromadb-vs-faiss.md) |
| Why Gemini via Vertex AI (prod) / AI Studio (dev)? | [ADR-003](adr/003-gemini-vertex-sdk.md) |
| Why JWT for Dialogflow webhook auth? | [ADR-004](adr/004-jwt-webhook-auth.md) |
