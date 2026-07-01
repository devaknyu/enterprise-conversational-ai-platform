# Acme Corp IT Guide — VPN Access and Troubleshooting
# Document ID: IT-NET-003 | Category: vpn-guide | Last Updated: 2026-02-01

## Overview

Acme Corp uses **Cisco AnyConnect Secure Mobility Client** as its corporate VPN solution.
VPN access is required to connect to internal resources (file shares, intranet, internal
applications) when working remotely or from non-corporate networks.

## VPN Client Installation

### Windows

1. Open the Software Center from the Start menu
2. Search for "Cisco AnyConnect"
3. Click Install — no administrator rights required; IT has pre-approved this software
4. Once installed, launch AnyConnect from the system tray
5. Enter the VPN server address: `vpn.acme.internal`
6. Authenticate with your Acme Corp email and password, then approve the MFA prompt

### macOS

1. Navigate to https://itsupport.acme.internal/downloads
2. Download "AnyConnect macOS Installer"
3. Open the downloaded .pkg file and follow the installation wizard
4. Allow the AnyConnect system extension when prompted in System Settings → Privacy & Security
5. Launch AnyConnect and connect to `vpn.acme.internal`

### Linux (Ubuntu/Debian)

Contact the IT helpdesk for the Linux VPN package — manual installation is required.

## Connecting to the VPN

1. Open Cisco AnyConnect from your taskbar or Applications folder
2. If the server address is blank, enter: `vpn.acme.internal`
3. Click **Connect**
4. Enter your Acme Corp email address and password
5. Approve the Duo MFA push notification on your registered mobile device
6. Wait for the "Connected" status — this typically takes 10–20 seconds

## Troubleshooting Common VPN Issues

### Issue: "Connection Attempt Failed" or "Unable to Connect"

**Likely causes:** Network firewall blocking VPN, incorrect server address, expired password

**Steps to resolve:**
1. Verify the server address is exactly `vpn.acme.internal` (no https://, no trailing slash)
2. Confirm your Acme Corp password has not expired — try logging into Outlook Web Access
3. Try connecting from a different network (e.g., phone hotspot instead of home WiFi)
4. Disable any third-party firewalls or security software temporarily for testing
5. Restart the Cisco AnyConnect service: Windows → Services → "Cisco AnyConnect" → Restart
6. If none of the above work, contact the IT helpdesk

### Issue: VPN Connects But Internal Resources Are Inaccessible

**Likely causes:** Split tunneling configuration, DNS not resolving internal hostnames

**Steps to resolve:**
1. Confirm you are connected (AnyConnect shows "Connected" with a green lock)
2. Try accessing an internal resource by IP address instead of hostname
3. Run `nslookup acme.internal` — if it fails, the VPN DNS is not routing correctly
4. Disconnect and reconnect to force DNS refresh
5. Restart your computer with the VPN disconnected, then reconnect

### Issue: VPN Disconnects Frequently

**Likely causes:** Unstable network connection, sleep/hibernate interrupting the VPN tunnel

**Steps to resolve:**
1. Connect using a wired Ethernet connection instead of WiFi if possible
2. Change Windows power settings to prevent the network adapter from sleeping:
   Device Manager → Network Adapters → Your adapter → Power Management → uncheck "Allow the computer to turn off this device to save power"
3. Update Cisco AnyConnect to the latest version (IT Self-Service Portal → Downloads)
4. If the issue persists, submit an IT ticket for a VPN profile reset

### Issue: "Authentication Failed" or MFA Issues

**Steps to resolve:**
1. Confirm your password is correct by testing at https://login.acme.com
2. If your Duo device has changed, contact the helpdesk to re-enroll your MFA device
3. Ensure your phone's date and time are set to automatic/network time
4. Try using a Duo passcode instead of a push notification (open Duo Mobile app → passcode)

## VPN Usage Policies

- VPN is required for all access to internal Acme Corp resources from non-corporate networks
- Personal devices must be enrolled in Jamf (Mac) or Intune (Windows) before VPN access is granted
- The VPN must not be used to route personal internet traffic — split tunneling is configured to route only Acme Corp traffic through the VPN
- Simultaneous VPN sessions from more than one device require helpdesk approval

## Getting Help

- IT Support Chat: IT Support Assistant (this chat)
- Email: helpdesk@acme.com
- Phone: 5-HELP (5-4357)
