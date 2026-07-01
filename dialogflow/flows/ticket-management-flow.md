# Flow: Ticket Management

**Intents:** `it.ticket.create` (tag: `create`) and `it.ticket.status` (tag: `status`)
**Handler:** `TicketHandler` (single instance, branches on `fulfillment_info.tag`)
**Entities Required:**
- Create: `@sys.email` → `caller_id`, free-form → `short_description`
- Status: `@it.ticket-number` → `ticket_number`

---

## Conversation Design — Create Ticket

```
Employee: "I need to open a ticket" / "Log an issue" / "Create a support request"
    ↓
[Start Page — Ticket Create Branch]
    ↓
[Collect Issue Description] — Page
  Entry fulfillment: "I'll create a ticket for you. Briefly describe the issue."
  Parameters:
    short_description (free-form, required)
    caller_id (@sys.email, required — pre-filled from session if already collected)
    category (@it.category, optional — defaults to "General")
  Condition route: all required params FINAL → [Create Ticket]
    ↓
[Create Ticket] — Page
  Entry fulfillment: WEBHOOK CALL → it.ticket.create (tag: "create")
    - FastAPI extracts caller_id, short_description, category
    - Calls TicketService.create_ticket()
    - Returns: "IT ticket INC0001234 has been created: Cannot connect to VPN. Priority: 3 - Moderate."
  Route: → [End Session]
```

---

## Conversation Design — Check Ticket Status

```
Employee: "What's the status of INC0001234?" / "Check my ticket" / "Where is my ticket?"
    ↓
[Start Page — Ticket Status Branch]
    ↓
[Collect Ticket Number] — Page
  Entry fulfillment: "What's the ticket number? It starts with INC."
  Parameter: ticket_number (@it.ticket-number, required)
  Condition route: $page.params.status = "FINAL" → [Check Status]
    ↓
[Check Status] — Page
  Entry fulfillment: WEBHOOK CALL → it.ticket.status (tag: "status")
    - FastAPI extracts ticket_number from session params
    - Calls TicketService.get_ticket_status()
    - Returns: "Ticket INC0001234: In Progress. Assigned to: Network Team."
  Route: → [End Session]
```

---

## Entity Collection

| Parameter | Entity Type | Flow | Required |
|---|---|---|---|
| `caller_id` | `@sys.email` | Create | Yes |
| `short_description` | Free-form | Create | Yes |
| `category` | `@it.category` | Create | No (default: General) |
| `ticket_number` | `@it.ticket-number` | Status | Yes |

---

## Webhook Calls

| Page | Intent | Tag | Session Params |
|---|---|---|---|
| Create Ticket | `it.ticket.create` | `create` | `caller_id`, `short_description`, `category` |
| Check Status | `it.ticket.status` | `status` | `ticket_number` |

---

## Error Paths

| Scenario | Response |
|---|---|
| ServiceNow unavailable | `build_error_response()` — try again or contact IT directly |
| Ticket not found | `build_error_response()` — verify ticket number, shows the number |
| Missing params | Never reaches webhook — Dialogflow collects all required params first |

---

## Training Phrases (Sample)

**Create:**
- "I need to open a ticket"
- "Create a support request"
- "Log a new IT issue"
- "Submit a ticket for VPN problems"

**Status:**
- "Check my ticket status"
- "What's the status of INC0001234"
- "Where is my support request"
- "Update on INC0002345 please"
