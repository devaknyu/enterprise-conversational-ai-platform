# Sample Conversations

Representative dialogues showing what the IT Support Assistant can do.
These are used for demos, testing, and Dialogflow CX flow design validation.

---

## 1. Password Reset (Happy Path)

**Employee:** Hi, I need to reset my password.

**Assistant:** I can help with that. What is your Acme Corp email address?

**Employee:** john.doe@acme.com

**Assistant:** I've initiated a password reset for john.doe@acme.com. A reset link has been sent
to your registered email address. You should receive it within 5 minutes.
Reference: AD-RESET-84729301.

Is there anything else I can help you with?

---

## 2. Password Reset (User Not Found)

**Employee:** Reset my password please.

**Assistant:** I can help with that. What is your Acme Corp email address?

**Employee:** jdoe@personal-email.com

**Assistant:** I wasn't able to find an Acme Corp account for that email address.
Please use your @acme.com work email. If you believe this is an error,
contact the IT helpdesk at extension 5-HELP.

---

## 3. IT Ticket Creation

**Employee:** I need to create a ticket. My VPN keeps disconnecting every 20 minutes.

**Assistant:** I'll create a ticket for that. Let me gather a few details.

What operating system are you using? (Windows or macOS)

**Employee:** Windows 11.

**Assistant:** Got it. I've created IT ticket INC0001242 for you:

- **Issue:** VPN disconnects frequently on Windows 11
- **Priority:** 3 - Moderate
- **Status:** Open
- **Assigned to:** Network Support Team

You'll receive an email confirmation at john.doe@acme.com.
You can ask me for a status update anytime using your ticket number.

Is there anything else I can help with?

---

## 4. Ticket Status Query

**Employee:** Can you check the status of my ticket INC0001234?

**Assistant:** Here's the current status of INC0001234:

- **Description:** VPN connection failing after Windows update
- **Status:** In Progress
- **Priority:** 2 - High
- **Assigned to:** IT Support Team
- **Last updated:** Today at 11:45 AM

The team is actively investigating. You'll receive an email when there's an update.

---

## 5. IT Policy Question (RAG)

**Employee:** What are the password requirements? How long does it need to be?

**Assistant:** According to Acme Corp's Password Management Policy (IT-SEC-001):

Your password must be at least **12 characters** long and include:
- At least 1 uppercase letter (A–Z)
- At least 1 lowercase letter (a–z)
- At least 1 number (0–9)
- At least 1 special character (such as ! @ # $ %)

Passwords expire every **90 days** for standard accounts. You'll receive reminder
emails 14 days and 3 days before expiration.

Would you like help resetting your password or have any other questions?

---

## 6. VPN Troubleshooting

**Employee:** My VPN isn't connecting. It says "Connection Attempt Failed."

**Assistant:** I can help troubleshoot that. Let me run a quick check on your VPN profile.

A few things to try:

1. **Verify the server address** is exactly `vpn.acme.internal` — no https:// prefix
2. **Check if your password has expired** — try logging in at https://login.acme.com
3. **Try a different network** — connect from your phone's hotspot instead of home WiFi to rule out a local firewall issue
4. **Restart the AnyConnect service:**
   - Press Win+R, type `services.msc`, press Enter
   - Find "Cisco AnyConnect" and click Restart

If none of these work, I can create an IT ticket for the network team to investigate.
Would you like me to do that?

**Employee:** Yes please.

**Assistant:** I've created ticket INC0001243 for your VPN connection issue.
The network support team will follow up within 4 hours. Ticket priority: 2 - High.

---

## 7. Escalation to Human Agent

**Employee:** I've tried everything and nothing is working. I need to talk to a real person.

**Assistant:** Understood — I'll connect you with a human IT support agent right away.

You're in position **3** in the queue. Estimated wait time: **8 minutes**.
Your session context has been shared with the agent so you won't need to repeat yourself.

While you wait, you can also reach the helpdesk directly at extension 5-HELP.
