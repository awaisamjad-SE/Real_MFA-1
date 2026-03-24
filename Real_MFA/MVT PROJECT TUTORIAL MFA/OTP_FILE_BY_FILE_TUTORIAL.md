# OTP App - File by File Tutorial

## 1) What this app does
OTP app is second factor gate:
- issue OTP
- verify OTP
- setup/verify TOTP
- resend with cooldown

## 2) models.py
Typical models:
- EmailOTP
- TOTPDevice
- BackupCode (optional)

Fields to include in EmailOTP:
- user
- code (hashed preferred)
- purpose
- expires_at
- attempts
- max_attempts
- is_used

Validation condition:
- not used
- not expired
- attempts below max

## 3) forms.py
Main forms:
- OTPVerifyForm
- TOTPVerifyForm
- TOTPSetupConfirmForm

Add clean methods for:
- code format (6 digits)
- required fields by context

## 4) views.py
Core views:
- otp_verify_view
- otp_resend_view
- totp_setup_view
- totp_confirm_view

Flow:
1. Read pending session values set by accounts login
2. Validate code
3. On success: finalize login
4. Clear pending keys

## 5) urls.py
Suggested routes:
- auth/mfa/verify/
- auth/mfa/resend/
- auth/totp/setup/
- auth/totp/confirm/

## 6) utils.py
Utility responsibilities:
- generate code
- hash/compare code
- expiry checks
- pyotp helpers for TOTP URI and verify

## 7) templates/otp/
Minimum:
- verify_otp.html
- setup_totp.html
- confirm_totp.html

## 8) security notes
- OTP validity 5 to 10 minutes
- resend cooldown 60 seconds
- max verify attempts per challenge
- audit every failure

## 9) mini exercise
1. build email OTP verify screen
2. add resend cooldown
3. add TOTP setup QR flow
4. add backup code fallback
