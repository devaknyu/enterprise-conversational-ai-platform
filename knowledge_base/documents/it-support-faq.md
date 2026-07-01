# Acme Corp IT Support — Frequently Asked Questions
# Document ID: IT-FAQ-001 | Category: it-support-faq | Last Updated: 2026-03-01

## Account & Access

**Q: How do I reset my password if I'm locked out?**
A: If you're completely locked out, call the IT helpdesk at extension 5-HELP (5-4357) from any Acme Corp desk phone or your personal mobile. The agent will verify your identity and issue a temporary password. For self-service resets when you can still access email, use the IT Self-Service Portal at https://itsupport.acme.internal. You can also ask this chat assistant to reset your password.

**Q: How long does it take to get access to a new system after onboarding?**
A: Standard application access is provisioned within 1 business day of your manager submitting the access request. For systems that require a security review (financial systems, HR systems, admin consoles), provisioning may take 3–5 business days. Your manager can track the status via the IT Self-Service Portal.

**Q: My account is disabled after being on leave. What do I do?**
A: Accounts are automatically disabled after 30 days of inactivity as a security measure. Contact the IT helpdesk with your employee ID and your manager's name. We will re-enable your account after verifying with your manager that you have returned.

**Q: How do I request access to a shared drive or SharePoint site?**
A: Submit an Access Request via the IT Self-Service Portal. Your manager must approve the request. Access is typically granted within 1 business day of approval.

## Hardware & Equipment

**Q: My laptop is running slowly. What should I do?**
A: Try these steps in order: (1) Restart your computer — this clears memory and applies pending updates. (2) Check for updates in Software Center and install any pending ones. (3) Use Task Manager (Windows) or Activity Monitor (Mac) to identify CPU or memory-hungry processes. (4) If the issue persists, submit an IT ticket and we will schedule a remote troubleshooting session.

**Q: How do I request a new laptop or hardware upgrade?**
A: Hardware requests require manager approval and go through the IT procurement process. Submit a Hardware Request via the IT Self-Service Portal with your business justification. Standard laptops are fulfilled within 5 business days; specialized hardware (developer workstations, high-RAM machines) may take 2–3 weeks.

**Q: My monitor isn't working. Is there a self-service fix?**
A: First, check the cable connections at both the monitor and the laptop/dock. Try pressing Win+P (Windows) or Command+F1 (Mac) to cycle display modes. Restart your laptop with the monitor connected. If none of these work, submit an IT ticket for a technician visit.

## Email & Communication

**Q: I'm not receiving emails. What should I check?**
A: Check your spam/junk folder first. Verify your mailbox isn't over the 50GB quota (Outlook → File → Account Settings → mailbox usage). Confirm you're not in Offline Mode (Outlook status bar should not say "Working Offline"). If these checks don't resolve it, contact the helpdesk.

**Q: How do I set up email on my mobile device?**
A: Install the Microsoft Outlook app from the App Store or Google Play. Sign in with your Acme Corp email and password. You will be prompted to enroll your device in Intune (Android) or Jamf (iOS) — this is required to access corporate email on personal devices. Contact the helpdesk if you need assistance.

**Q: Can I use personal email for Acme Corp business?**
A: No. Acme Corp data must not be sent to or stored in personal email accounts. This is a security and compliance requirement. Use only your @acme.com email address for all business communication.

## VPN & Remote Access

**Q: Do I need VPN to work from home?**
A: Yes, VPN is required to access internal Acme Corp resources (file servers, intranet, internal applications). Microsoft 365 (Teams, Outlook, SharePoint) does not require VPN. Install Cisco AnyConnect and connect to vpn.acme.internal before accessing internal resources.

**Q: The VPN connects but I can't access the intranet. What's wrong?**
A: This is usually a DNS resolution issue. Disconnect and reconnect the VPN. If the issue persists, run `nslookup acme.internal` from the command prompt. If it fails, contact the helpdesk — your VPN DNS configuration may need to be reset.

## Software & Applications

**Q: How do I install software on my laptop?**
A: Use Software Center (Windows) or Managed Software Center (macOS) for any software in the approved catalog — no IT ticket required. For software not in the catalog, submit a Software Request via the IT Self-Service Portal. Unauthorized software installations are a policy violation.

**Q: A software application is crashing repeatedly. What should I do?**
A: (1) Restart the application. (2) Check for updates in Software Center. (3) Restart your computer. (4) Uninstall and reinstall via Software Center. If none of these work, submit an IT ticket with the application name, error message (screenshot if possible), and steps to reproduce.

## IT Tickets

**Q: How do I check the status of an IT ticket?**
A: You can ask this chat assistant for your ticket status — just say "check status of INC followed by your ticket number." Alternatively, log in to the IT Self-Service Portal at https://itsupport.acme.internal to view all your open tickets.

**Q: What are the IT ticket priority levels?**
A: Priority 1 (Critical) — complete business disruption affecting multiple employees; response within 1 hour. Priority 2 (High) — major functionality impaired affecting an individual; response within 4 hours. Priority 3 (Moderate) — partial disruption with workaround available; response within 1 business day. Priority 4 (Low) — minor inconvenience; response within 3 business days.
