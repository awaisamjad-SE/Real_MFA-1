# Notification App (MVT)

## Purpose
The `notification` app manages user security communications (email/SMS/in-app logs).

## Key Files

### models.py
- `EmailNotification`: to, subject, body, status.
- `NotificationLog`: event channel log and metadata.
- `NotificationPreference`: user opt-in settings.

### services.py or utils.py
- Composes and sends messages.
- Keeps provider details isolated from views.
- Adds retries and fallback behavior.

### templates/notification/email/
- HTML templates for each alert type:
  - verification
  - otp
  - password change
  - new device

### admin.py
- Lets support/admin inspect delivery status.

## Common Bugs
- Writing non-JSON data into JSON fields.
- Unique provider message id collisions.
- Breaking user requests when notification send fails.

## Reliability Pattern
1. Business flow executes first.
2. Notification write/send in safe block.
3. On failure: log and continue if non-critical.

## Security Notes
- Avoid leaking secrets in email body.
- Do not log full OTP/token in production.
- Store provider IDs for traceability.

## March 2026 Practical Fixes

1. JSON metadata safety:
- Before saving to JSONField, coerce metadata into JSON-safe values.
- Use a JSON encoder for datetime/decimal/uuid-like values.

2. Unique provider message IDs:
- If mail backend does not return provider id, generate one in app code.
- Keep uniqueness at model level to prevent duplicate insert failures.

3. Error isolation:
- Notification send/log errors should not crash registration or login when notification is non-critical.
- Wrap send/log operations in safe handling and record compact diagnostic info.
