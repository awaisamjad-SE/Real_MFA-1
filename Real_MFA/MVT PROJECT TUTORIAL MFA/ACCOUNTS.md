# Accounts App (MVT)

## Purpose
The `accounts` app handles identity and profile-level security in a Django MVT MFA project.

## Key Files

### models.py
- Defines custom `User` model (email login, role, security flags).
- Defines `Profile` and optional `PasswordHistory`.
- Adds account lock fields (`failed_login_attempts`, `account_locked_until`).

### urls.py
- App routes for auth pages.
- Typical paths: register, login, logout, dashboard, profile.

### views.py
- MVT controller functions.
- Handles form submit and template render.
- Creates pending MFA state in session after password verification.

### forms.py
- `RegisterForm`, `LoginForm`, `ProfileForm`, `PasswordChangeForm`.
- Keeps input validation centralized.

### backends.py (optional)
- Custom auth backend for email-based login.

### signals.py
- Auto-create profile on user creation.
- Optional account event hooks (password changed, mfa state changed).

### admin.py
- Registers User/Profile with filters and search.
- Useful for moderation and support workflow.

## Request Flow (Example: Login)
1. User opens login template.
2. `LoginForm` validates credentials.
3. View checks lock status and verification status.
4. If MFA enabled, set session `pending_user_id` and redirect to OTP view.
5. If no MFA, call `login(request, user)` and redirect dashboard.

## Common Bugs
- Using default `User` while project expects custom user.
- Creating custom user after migrations already applied.
- Missing `AUTH_USER_MODEL` in settings.

## Security Notes
- Enforce strong password validators.
- Add lockout and cooldown policy.
- Always audit failed login attempts.

## March 2026 Practical Fixes

1. Superuser verification default:
- If email verification is enforced by custom auth backend, create superuser with verified email state.

2. Safe registration save path:
- Wrap serializer/form save path with controlled exception handling.
- Return consistent API/UI error response instead of raw HTTP 500.

3. Host/origin alignment for auth forms:
- Keep `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `CORS_ALLOWED_ORIGINS` aligned with the public domain.
