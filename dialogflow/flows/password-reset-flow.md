# Flow: Password Reset

**Intent:** `it.password.reset`
**Handler:** `PasswordHandler`
**Entity Required:** `@sys.email` → session parameter `user_id`

---

## Conversation Design

```
Employee: "I need to reset my password" / "Can't log in" / "Locked out"
    ↓
[Start Page] — Default Welcome Intent routes here
    ↓
[Collect Employee Email] — Page
  Entry fulfillment: "I can help with that. What's your work email address?"
  Parameter: user_id (@sys.email, required)
  Condition route: $page.params.status = "FINAL" → [Confirm Reset]
    ↓
[Confirm Reset] — Page
  Entry fulfillment: WEBHOOK CALL → it.password.reset
    - FastAPI extracts user_id from session_info.parameters
    - Calls PasswordService.initiate_reset()
    - Returns: "Your password reset has been sent to your email. Reference: INC0001234."
  Route: → [End Session]
```

---

## Entity Collection

| Parameter | Entity Type | Required | Prompt |
|---|---|---|---|
| `user_id` | `@sys.email` | Yes | "What's your work email address?" |

---

## Webhook Call

- **Page:** Confirm Reset (entry fulfillment)
- **Tag:** _(not used — single action per intent)_
- **Session parameters forwarded:** `user_id`
- **Fulfillment message:** From `PasswordHandler.handle()` via `ResponseBuilder.build_password_reset_response()`

---

## Error Paths

| Scenario | Dialogflow Response |
|---|---|
| User not found in AD | `build_password_reset_user_not_found()` — verify employee ID |
| AD integration failure | `build_error_response()` — try again or contact IT |
| Missing `user_id` | Never reaches webhook — Dialogflow collects before calling |

---

## Training Phrases (Sample)

- "I need to reset my password"
- "My password isn't working"
- "I'm locked out of my account"
- "Can't log into Windows"
- "Forgot my AD password"
- "Password expired"
- "Reset password for john.doe@acme.com"

---

## Transition Routes

| Condition | Target |
|---|---|
| Webhook succeeds | End Session (employee gets fulfillment message) |
| No-match x2 | `it.escalate` flow (hand off to human agent) |
| Employee says "cancel" / "nevermind" | Default Cancel handler |
