# Dialogflow CX Agent

This directory contains the Dialogflow CX agent configuration and export.

## Agent Export

The agent export (JSON/ZIP) lives in `agent-export/`. Import it into a new
Dialogflow CX agent to restore all intents, flows, entities, and pages.

## Configured Intents

| Intent Display Name | Fulfillment Handler | Description |
|---|---|---|
| `it.password.reset` | PasswordHandler | Employee password reset via Active Directory |
| `it.ticket.create` | TicketHandler | Create a new IT support incident in ServiceNow |
| `it.ticket.status` | TicketHandler | Query the status of an existing ticket |
| `it.vpn.troubleshoot` | VPNHandler | VPN connectivity diagnostics and guided fixes |
| `it.policy.query` | RAGHandler | Policy questions answered via RAG + Gemini |
| `it.escalate` | EscalationHandler | Transfer conversation to a human agent |

## Webhook Configuration

After deploying the FastAPI application to Cloud Run:

1. In Dialogflow CX Console → Agent Settings → Webhooks
2. Create a new webhook named `it-assistant-webhook`
3. Set the URL to your Cloud Run service URL + `/webhook`
   Example: `https://it-assistant-xyz-uc.a.run.app/webhook`
4. Under Authentication, select **Bearer Token**
5. Generate a token: `python scripts/generate_jwt.py`
6. Paste the generated token into the Bearer Token field
7. Save and test with the Dialogflow CX test console

## Flow Documentation

See `flows/` for human-readable documentation of each conversation flow.

## Local Testing (Without Dialogflow)

During development, you can test the webhook directly without a Dialogflow agent:

```bash
# Generate a test JWT
python scripts/generate_jwt.py

# Send a test webhook request
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <generated-token>" \
  -d @dialogflow/flows/test-password-reset.json
```
