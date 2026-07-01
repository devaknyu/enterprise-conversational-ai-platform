# Acme Corp IT Security Policy — Password Management
# Document ID: IT-SEC-001 | Category: password-policy | Last Updated: 2026-01-15

## Overview

This policy governs the creation, management, and protection of passwords for all Acme Corp
information systems, applications, and network resources. All employees, contractors, and
third-party vendors with access to Acme Corp systems must comply with this policy.

## Password Complexity Requirements

All user passwords must meet the following minimum requirements:

- **Minimum length:** 12 characters
- **Maximum length:** 128 characters
- **Uppercase letters:** At least 1 required (A–Z)
- **Lowercase letters:** At least 1 required (a–z)
- **Numbers:** At least 1 required (0–9)
- **Special characters:** At least 1 required from: `! @ # $ % ^ & * ( ) - _ = + [ ] { } ; : ' " , . < > / ?`
- **No spaces** are permitted in passwords
- Passwords must not contain your username, first name, last name, or employee ID
- Passwords must not be one of your previous 12 passwords

## Password Expiration

- Standard user accounts: passwords expire every **90 days**
- Privileged/admin accounts: passwords expire every **30 days**
- Service accounts: passwords expire every **180 days**
- You will receive email reminders at 14 days and 3 days before expiration

## Password Reset Procedures

**Self-service reset (preferred):**
1. Navigate to the IT Self-Service Portal at https://itsupport.acme.internal
2. Click "Forgot Password" and enter your employee email address
3. Check your registered mobile device for an MFA verification code
4. Follow the prompts to create a new password

**Assisted reset via IT helpdesk:**
- Contact the IT helpdesk at extension 5-HELP or helpdesk@acme.com
- The helpdesk agent will verify your identity using your employee ID and manager's name
- A temporary password will be sent to your registered mobile number
- You must change the temporary password on your first login

**Automated reset via chat assistant:**
- Type "reset my password" in the IT support chat
- Provide your employee email address when prompted
- A reset link will be sent to your registered email within 5 minutes

## Account Lockout Policy

- Accounts are locked after **5 consecutive failed login attempts**
- Lockout duration: **30 minutes** (automatic unlock)
- For immediate unlock, contact the IT helpdesk or use the self-service portal

## Prohibited Password Practices

The following are strictly prohibited:

- Writing passwords on paper or storing them in unencrypted files
- Sharing passwords with colleagues, managers, or IT staff
- Using the same password for Acme Corp accounts and personal accounts
- Using dictionary words, keyboard patterns (e.g. "qwerty"), or sequences (e.g. "12345678")
- Storing passwords in browsers on shared or public computers

## Approved Password Managers

Acme Corp approves the use of the following corporate password managers:

- **1Password for Business** (preferred) — provisioned by IT, contact helpdesk to request access
- **LastPass Enterprise** — legacy accounts only, migrating to 1Password

## Questions and Support

For password-related assistance, contact the IT helpdesk:
- Chat: IT Support Assistant (this chat)
- Email: helpdesk@acme.com
- Phone: extension 5-HELP (5-4357)
- Hours: Monday–Friday 7:00 AM – 8:00 PM ET; Emergency support 24/7
