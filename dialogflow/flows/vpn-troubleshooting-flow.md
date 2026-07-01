# Flow: VPN Troubleshooting

**Intent:** `it.vpn.troubleshoot`
**Handler:** `VPNHandler`
**Entities Required:** `@sys.email` → `user_id`; `@it.vpn-symptom` (list) → `symptoms`

---

## Conversation Design

```
Employee: "VPN isn't working" / "Can't connect to VPN" / "VPN keeps disconnecting"
    ↓
[Start Page — VPN Branch]
    ↓
[Collect VPN Symptoms] — Page
  Entry fulfillment: "I can help troubleshoot your VPN issue.
                      Are you seeing an error message, or describe what's happening."
  Parameters:
    user_id   (@sys.email, required — pre-filled if already in session)
    symptoms  (@it.vpn-symptom, list, optional)
  Condition route: user_id FINAL → [Run Diagnostics]
    ↓
[Run Diagnostics] — Page
  Entry fulfillment: WEBHOOK CALL → it.vpn.troubleshoot
    - FastAPI extracts user_id, symptoms (list)
    - Calls VPNService.diagnose()
    - If escalate=False:  Returns diagnosis + numbered remediation steps
    - If escalate=True:   Returns steps + advisory to escalate to IT specialist
    ↓
[Escalate Branch] — conditional route on response text / session param
  If escalate flag set in session: Route → Escalation Flow
  Else: → [End Session]
```

---

## Entity Collection

| Parameter | Entity Type | Required | Notes |
|---|---|---|---|
| `user_id` | `@sys.email` | Yes | Used to look up VPN profile in gateway |
| `symptoms` | `@it.vpn-symptom` (list) | No | Enriches diagnostic context |

### `@it.vpn-symptom` Entity Values

| Canonical | Synonyms |
|---|---|
| `cannot connect` | can't connect, fails to connect, won't connect |
| `slow` | slow speed, poor performance, latency, lag |
| `disconnects` | keeps dropping, disconnecting, unstable |
| `auth failed` | authentication error, credentials rejected, login failed |
| `certificate error` | cert error, SSL error, security warning |

---

## Webhook Call

- **Page:** Run Diagnostics (entry fulfillment)
- **Tag:** _(not used)_
- **Session parameters forwarded:** `user_id`, `symptoms`
- **Fulfillment messages:**
  - No escalation: `build_vpn_response(diagnosis, steps)`
  - Escalation needed: `build_vpn_escalation_response(diagnosis, steps)`

---

## Error Paths

| Scenario | Response |
|---|---|
| VPN gateway unreachable | `build_error_response()` — contact IT directly |
| Integration timeout | Same as above (caught by `IntegrationError`) |
| No symptoms provided | Handled gracefully — `symptoms=[]` still runs diagnostics |

---

## Transition Routes

| Condition | Target |
|---|---|
| VPN issue resolved by steps | End Session |
| Diagnostics indicate escalation | Route to `it.escalate` flow |
| No-match x2 | Route to `it.escalate` flow |

---

## Training Phrases (Sample)

- "VPN isn't working"
- "I can't connect to the company VPN"
- "VPN keeps disconnecting"
- "Authentication failed on VPN"
- "VPN is very slow today"
- "I get a certificate error when connecting to VPN"
- "Remote access not working"
