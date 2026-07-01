# Acme Corp IT Policy — Software Installation and Licensing
# Document ID: IT-SW-002 | Category: software-policy | Last Updated: 2026-01-20

## Overview

This policy governs the installation, use, and licensing of software on all Acme Corp
managed devices. Unauthorized software installation creates security risks, compliance
liabilities, and licensing violations. All employees must follow this policy.

## Approved Software Catalog

Acme Corp maintains an approved software catalog accessible through:
- **Windows:** Software Center (Start menu → Software Center)
- **macOS:** Managed Software Center (Applications → Managed Software Center)

Software in the catalog is pre-licensed, security-approved, and can be installed without
IT helpdesk involvement. The catalog includes:

| Category | Approved Software |
|---|---|
| Productivity | Microsoft 365 (Word, Excel, PowerPoint, Teams, Outlook) |
| Development | VS Code, JetBrains IDEs (IntelliJ, PyCharm, WebStorm), Git, Docker Desktop |
| Communication | Microsoft Teams, Zoom, Slack (approved departments only) |
| Design | Adobe Creative Cloud (licensed seats — request via helpdesk) |
| Security | CrowdStrike Falcon, 1Password for Business, Duo Mobile |
| Browsers | Google Chrome, Microsoft Edge, Firefox |
| Diagramming | Lucidchart, draw.io |

## Requesting Software Not in the Catalog

If you need software not in the approved catalog:

1. Submit a Software Request via the IT Self-Service Portal or this chat ("I need to install [software name]")
2. Provide the business justification for the request
3. IT Security reviews the software for security and compliance within 5 business days
4. If approved, IT Procurement validates the licensing model
5. Approved software is added to the catalog or installed by an IT technician

**Expedited requests:** For business-critical needs, contact your manager to escalate with IT leadership.

## Prohibited Software

The following categories of software are **strictly prohibited** on Acme Corp devices:

- **Peer-to-peer file sharing:** BitTorrent clients, uTorrent, LimeWire
- **Remote access tools not approved by IT:** TeamViewer (personal), AnyDesk (personal), LogMeIn
- **Cryptocurrency mining software**
- **Personal VPN clients** (use only the Acme Corp Cisco AnyConnect VPN)
- **Unlicensed or cracked software** of any kind
- **Browser extensions not in the approved list** (security team maintains the approved extension list)

Violation of this policy may result in disciplinary action and device reimaging.

## Software Licensing Compliance

- All software must be used in accordance with its license agreement
- Do not install software on more devices than the license permits
- Do not share license keys or activation codes
- License usage is audited quarterly; over-use triggers mandatory removal
- If you need additional licenses for your team, submit a request via the IT portal

## macOS and Windows Update Policy

- Operating system updates are pushed automatically by IT via Jamf (macOS) and Intune (Windows)
- Feature updates (major OS versions) are deployed to pilot groups first, then broadly
- Security patches are deployed within 72 hours of release — do not postpone these
- Devices not updated within 14 days of a mandatory patch are quarantined from the network

## Getting Help with Software

- Self-service installs: Use Software Center or Managed Software Center
- Request new software: IT Self-Service Portal or this chat
- Installation issues: Contact the IT helpdesk at extension 5-HELP
- License questions: it-licensing@acme.com
