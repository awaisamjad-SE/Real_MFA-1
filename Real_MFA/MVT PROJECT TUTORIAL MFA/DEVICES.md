# Devices App (MVT)

## Purpose
The `devices` app tracks user devices and trust state for adaptive MFA.

## Key Files

### models.py
- `Device`: fingerprint, browser, OS, IP, trust flags.
- `TrustedDevice` (optional separate table).
- `Session` model for active session tracking.

### urls.py
- Device list/manage routes.
- Example: `/devices/`, `/devices/trust/<id>/`, `/devices/revoke/<id>/`.

### views.py
- List user devices.
- Mark trust/untrust.
- Revoke session(s) from a device.

### utils.py
- User-agent parsing helpers.
- Device risk score helpers.
- Device fingerprint normalization.

### signals.py
- On new device, trigger security alert.
- On trust state changes, create audit log.

## Flow (New Device Login)
1. Device fingerprint not recognized.
2. Mark as untrusted.
3. Enforce MFA challenge.
4. After success, optionally trust device for N days.

## Common Bugs
- Not expiring trust windows.
- Missing unique constraint on user+fingerprint.
- Blindly trusting first-seen device without MFA.

## Security Notes
- Never trust device on password-only login.
- Allow users to view and revoke all devices.
- Track compromised flag for high-risk anomalies.
