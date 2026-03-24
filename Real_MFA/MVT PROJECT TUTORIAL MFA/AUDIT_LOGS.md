# Audit Logs App (MVT)

## Purpose
The `audits_logs` app records security-sensitive events for observability and compliance.

## Key Files

### models.py
- `AuditLog` model with:
  - actor/user
  - event type
  - ip/user agent
  - metadata JSON
  - timestamp

### views.py (optional)
- Admin-only event viewer with filters.

### admin.py
- Read-only listing and filtering.

## Events to Capture
- register success/failure
- login success/failure
- otp verify success/failure
- password reset start/complete
- mfa enabled/disabled
- device trusted/revoked

## Common Bugs
- Logging too little context to debug incidents.
- Logging sensitive secrets directly.
- No retention/cleanup policy.

## Security Notes
- Keep metadata JSON-safe.
- Avoid storing plaintext passwords/tokens.
- Add index by event type + created_at for query speed.
