# OTP App (MVT)

## Purpose
The `otp` app provides second-factor verification by email OTP and/or TOTP.

## Key Files

### models.py
- Stores OTP records with expiry and attempts.
- Stores TOTP setup data (secret, enabled state).
- Optional backup recovery codes.

### urls.py
- Routes for OTP verify pages.
- Example: `/auth/mfa/verify/`, `/auth/totp/setup/`, `/auth/totp/confirm/`.

### views.py
- Reads pending login state from session.
- Verifies OTP/TOTP and finalizes login.
- Handles resend logic with cooldown.

### forms.py
- OTP code entry form.
- TOTP verification form.
- Optional trust-device checkbox.

### utils.py
- OTP generation and hashing helpers.
- Expiry checks and attempt increment logic.
- TOTP provisioning URI and QR generation helpers.

## Request Flow (Example: Email OTP)
1. Password phase succeeds in accounts app.
2. Session stores pending user.
3. OTP app sends code and renders verify page.
4. User submits code.
5. View validates code, expiry, and attempts.
6. On success, complete login.

## Common Bugs
- Storing OTP as plain text without expiry check.
- No max attempts, allowing brute force.
- Final login done without clearing pending session keys.

## Security Notes
- OTP should be short-lived (e.g., 5-10 mins).
- Limit verify attempts and resend frequency.
- Log every OTP verify failure.
