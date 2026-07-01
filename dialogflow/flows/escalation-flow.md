# Flow: Human Agent Escalation

**Intent:** `it.escalate`
**Handler:** `EscalationHandler`
**Entities:** `@sys.email` → `user_id`; free-form → `reason`

---

## Conversation Design

```
Employee: "I need to speak to someone" / "Let me talk to a person" / "This isn't helping"
    ↓
[Entry — Escalation Requested]
  Triggered by:
    a) Employee explicitly says "talk to a person / agent / human"
    b) No-match x2 fallback from any other flow
    c) VPNHandler returns escalate=True (session param set, flow transition)
    ↓
[Collect Escalation Reason] — Page
  Entry fulfillment: "I'll connect you with an IT specialist. Can you briefly describe your issue?"
  Parameters:
    user_id   (@sys.email, required — pre-filled if already in session)
    reason    (free-form, optional — defaults to "Employee requested escalation")
  Condition route: user_id FINAL → [Escalate]
    ↓
[Escalate] — Page
  Entry fulfillment: WEBHOOK CALL → it.escalate
    - FastAPI extracts user_id, reason
    - Calls EscalationService.escalate()
    - Creates high-priority ServiceNow ticket (priority: "2 - High", category: "Escalation")
    - Returns queue position and estimated wait time
    - Example: "I've escalated your request. You're #2 in the queue (~10 min wait)."
  Route: → [End Session]
```

---

## Entity Collection

| Parameter | Entity Type | Required | Notes |
|---|---|---|---|
| `user_id` | `@sys.email` | Yes | Used for agent context handoff and ticket creation |
| `reason` | Free-form | No | Summarizes the issue for the human agent |

---

## Webhook Call

- **Page:** Escalate (entry fulfillment)
- **Tag:** _(not used)_
- **Session parameters forwarded:** `user_id`, `reason`
- **Fulfillment message:** `build_escalation_response(queue_position, estimated_wait_minutes)`

---

## Error Paths

| Scenario | Response |
|---|---|
| Escalation queue unavailable | `build_error_response()` — advises employee to call IT directly |

---

## Transition Routes

| Source | Trigger |
|---|---|
| Any flow | Employee says "talk to a person", "human", "agent", "real person" |
| Any flow | No-match x2 or no-input x2 (configured in Default Fallback) |
| VPN Flow | Session param `vpn_escalate=true` set by VPNHandler |

---

## Context Handoff

When `EscalationService.escalate()` creates the ServiceNow ticket, it embeds:
- Employee `user_id`
- Dialogflow `session_id` (allows the human agent to pull conversation history)
- `reason` summary

This gives the human agent full context without the employee repeating themselves —
a key enterprise UX requirement.

---

## Training Phrases (Sample)

- "I want to talk to a real person"
- "Can I speak to someone"
- "Connect me to IT support"
- "This bot isn't helping"
- "Let me talk to an agent"
- "Transfer me to a human"
- "I need human assistance"
- "Escalate my issue"
