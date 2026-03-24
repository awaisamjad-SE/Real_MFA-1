# MVT PROJECT TUTORIAL MFA

## Contents

1. `ACCOUNTS.md`
- Accounts app structure and file responsibilities.

2. `OTP.md`
- OTP/TOTP app structure and flow.

3. `DEVICES.md`
- Device trust and session tracking app.

4. `NOTIFICATION.md`
- Notification models, services, templates, reliability notes.

5. `AUDIT_LOGS.md`
- Security event logging design.

6. `PROJECT.md`
- End-to-end app wiring, missing pieces, and advanced/DSA concepts.

7. `ACCOUNTS_FILE_BY_FILE_TUTORIAL.md`
- Step-by-step tutorial for accounts models/forms/views/urls/templates.

8. `OTP_FILE_BY_FILE_TUTORIAL.md`
- Step-by-step tutorial for OTP and TOTP implementation files.

9. `DEVICES_FILE_BY_FILE_TUTORIAL.md`
- Device/session/trust file guide and implementation order.

10. `NOTIFICATION_FILE_BY_FILE_TUTORIAL.md`
- Notification models/services/templates and reliability patterns.

11. `AUDIT_LOGS_FILE_BY_FILE_TUTORIAL.md`
- Audit event model and integration points across the project.

## How to Use This Folder

1. Read `PROJECT.md` first for system overview.
2. Then read each app file and map it to your codebase.
3. Implement app-by-app and test each flow before moving to next.

## March 2026 Update Notes

Use these docs with the latest project runtime assumptions:

1. Domain setup now targets `awaisamjad.engineer` and `www.awaisamjad.engineer`.
2. Production env should include matching `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `CORS_ALLOWED_ORIGINS`.
3. Containerized deployments must not use localhost for DB/Redis inside Docker network.
4. Notification metadata must always be JSON-safe before saving to JSON fields.
5. Email provider message IDs should be generated uniquely when provider does not return one.
