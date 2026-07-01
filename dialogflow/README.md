# Dialogflow CX Agent — Enterprise IT Support Assistant

This directory contains the Dialogflow CX agent configuration, flow documentation, and a
reference agent export skeleton. All business logic lives in the FastAPI webhook layer —
Dialogflow CX is responsible only for NLU, conversation state, and routing to fulfillment.

## Architecture Principle

> Dialogflow CX owns conversation state. FastAPI owns all data operations.

Dialogflow resolves the employee's intent and extracts entities (user ID, ticket number,
symptoms). FastAPI executes the business logic (AD lookups, ServiceNow calls, VPN diagnostics)
and returns the fulfillment response. Zero business logic lives in Dialogflow flows.

---

## Configured Intents

| Intent Display Name | Fulfillment Tag | Handler | Description |
|---|---|---|---|
| `it.password.reset` | _(none)_ | `PasswordHandler` | Employee password reset via Active Directory |
| `it.ticket.create` | `create` | `TicketHandler` | Create a new IT support incident in ServiceNow |
| `it.ticket.status` | `status` | `TicketHandler` | Query the status of an existing ticket |
| `it.vpn.troubleshoot` | _(none)_ | `VPNHandler` | VPN connectivity diagnostics and guided remediation |
| `it.policy.query` | _(none)_ | `RAGHandler` | Policy questions answered via RAG + Gemini (Phase 6) |
| `it.escalate` | _(none)_ | `EscalationHandler` | Transfer conversation to a human IT agent |

**Fulfillment tags:** `TicketHandler` handles two intents using the `fulfillment_info.tag`
field to branch between create and status logic. Other handlers are registered per intent.

---

## Entity Types

| Entity | Type | Example Values |
|---|---|---|
| `@sys.email` | System | `john.doe@acme.com` |
| `@it.ticket-number` | Custom (Regexp) | `INC\d{7}` |
| `@it.vpn-symptom` | Custom (Enum) | `cannot connect`, `slow`, `disconnects`, `auth failed` |
| `@it.escalation-reason` | Custom (Free-form) | Any employee-supplied text |

---

## Agent Export

`agent-export/agent.json` contains a skeleton of the Dialogflow CX REST API agent structure.
This is a reference document demonstrating the agent schema — to use it in a live Dialogflow
CX project, populate the `name` and `parent` fields with your GCP project details and import
via the Dialogflow CX console or the REST API.

---

## Webhook Configuration

After deploying the FastAPI service to Cloud Run:

1. In Dialogflow CX Console → Agent Settings → Webhooks
2. Create a webhook named `it-assistant-webhook`
3. Set the URL to your Cloud Run service URL + `/webhook/`
   - Example: `https://it-assistant-xyz-uc.a.run.app/webhook/`
4. Under Authentication → **Bearer Token**
5. Generate a token: `python scripts/generate_jwt.py`
6. Paste the generated token into the Bearer Token field
7. On each page where fulfillment is needed:
   - Entry fulfillment → Enable webhook → Select `it-assistant-webhook`
   - Set **Tag** to the value in the Fulfillment Tag column above (e.g. `create`)

---

## Local Development Testing (Without a Live Dialogflow Agent)

You can test the webhook directly using curl or httpx without a Dialogflow agent:

```bash
# 1. Start the FastAPI server
uvicorn app.main:app --reload

# 2. Generate a test JWT
python scripts/generate_jwt.py

# 3. Send a password reset test request
curl -X POST http://localhost:8000/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <generated-token>" \
  -d '{
    "detect_intent_response_id": "test-001",
    "intent_info": {
      "display_name": "it.password.reset",
      "parameters": {},
      "confidence": 0.99
    },
    "session_info": {
      "session": "projects/test/agents/test/sessions/local-test",
      "parameters": {"user_id": "john.doe@acme.com"}
    },
    "fulfillment_info": {"tag": ""},
    "page_info": {},
    "text": "I need to reset my password"
  }'

# 4. Send a ticket creation test request
curl -X POST http://localhost:8000/webhook/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <generated-token>" \
  -d '{
    "intent_info": {"display_name": "it.ticket.create", "parameters": {}},
    "fulfillment_info": {"tag": "create"},
    "session_info": {
      "session": "projects/test/agents/test/sessions/local-test",
      "parameters": {
        "caller_id": "john.doe@acme.com",
        "short_description": "Cannot connect to VPN from home office"
      }
    },
    "page_info": {}, "text": ""
  }'
```

---

## Flow Documentation

See `flows/` for human-readable documentation of each conversation flow, including
page sequences, entity collection steps, and transition conditions.
