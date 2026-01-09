# Registration + Email Verification (Backend)

This document explains how registration, email verification, and resend verification work in this project.

## Key URLs

- API base: `http://127.0.0.1:8000/api/`
- Register: `POST /auth/register/`
- Verify email: `POST /auth/verify-email/`
- Resend verification: `POST /auth/resend-verification-email/`

Project URL routing:
- The project routes `path('api/', include('accounts.urls'))`.
- The accounts app exposes the endpoints under `auth/*`.

## Environment (.env)

### Where the `.env` file must be

Put `.env` here (same folder as `manage.py`):

- `Real_MFA/Real_MFA/.env`

### How `.env` gets loaded

`Real_MFA.settings` loads `BASE_DIR / '.env'` at startup using `python-dotenv`. This makes variables like `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `FRONTEND_URL`, `REDIS_HOST`, etc. available via `os.getenv()`.

### Minimum recommended `.env` keys for this flow

**Do not commit real secrets.**

- `DEBUG=True`
- `FRONTEND_URL=http://localhost:3000`
- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST=smtp.gmail.com`
- `EMAIL_PORT=587`
- `EMAIL_USE_TLS=True`
- `EMAIL_HOST_USER=<your gmail>`
- `EMAIL_HOST_PASSWORD=<gmail app password>`
- `REDIS_HOST=localhost`
- `REDIS_PORT=6379`
- `REDIS_DB=0`
- `CELERY_BROKER_URL=redis://localhost:6379/0`
- `CELERY_RESULT_BACKEND=redis://localhost:6379/0`

### Gmail note

For Gmail SMTP, `EMAIL_HOST_PASSWORD` should be a **Gmail App Password** (not your normal Gmail password).

## What happens during registration

### Endpoint

`POST /api/auth/register/`

Example request:

```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "phone_number": "+1234567890",
  "device": {
    "fingerprint_hash": "abcdef12345",
    "device_type": "mobile",
    "browser": "Safari",
    "os": "iOS"
  }
}
```

Example response:

```json
{
  "id": "<uuid>",
  "email": "john@example.com",
  "username": "john",
  "message": "Registration successful. Check your email to verify.",
  "device_id": "<uuid>"
}
```

### Validation

- Passwords must match (`password` == `password2`).
- Username and email must be unique.
- `device.fingerprint_hash` must be at least 10 characters.

### Data created

- A new `accounts.User` is created.
- A `accounts.Profile` is auto-created by signals.
- A `devices.Device` record is created for the device payload.

### Token storage

- A verification token is generated using Django’s `default_token_generator`.
- The token is stored under the key:
  - `verification_token:<user_id>`

Storage uses:
- Redis if reachable.
- Otherwise a cache-backed fallback (LocMemCache) for development.

### Email send

The task `send_verification_email(user_id)` is called via Celery.

The email contains a verification link like:

`<FRONTEND_URL>/verify-email/<uid>/<token>/`

**Important**: This is a frontend URL. The backend verification is done using the backend endpoint (see below).

## How to verify email

### Backend verification endpoint

`POST /api/auth/verify-email/`

Body:

```json
{
  "uid": "<base64 user id>",
  "token": "<token>"
}
```

Where do `uid` and `token` come from?

If the email link is:

`http://localhost:3000/verify-email/<uid>/<token>/`

Then copy those parts directly into the API request body.

### What verification does

- Decodes `uid` to a user id.
- Validates the `token` with `default_token_generator.check_token(user, token)`.
- Sets `user.email_verified = True`.
- Deletes the stored token key `verification_token:<user_id>`.

## How resend verification works

### Endpoint

`POST /api/auth/resend-verification-email/`

Body:

```json
{
  "email": "john@example.com"
}
```

### Rate limits

Resend is limited per user:

- Cooldown: 60 seconds between resends
- Hourly cap: max 4 resends/hour

Keys used:

- `resend_cooldown:<user_id>` (TTL 60s)
- `resend_limit:<user_id>` (TTL 3600s)

### What resend does

- Rejects if user not found.
- Rejects if already verified.
- Enforces cooldown and hourly limit.
- Invalidates previous token:
  - deletes `verification_token:<user_id>`
- Generates a new token and stores it again.
- Sends the verification email again.

## Celery behavior in development

### Eager mode

In `DEBUG=True`, Celery defaults to eager mode (runs tasks inline) unless you set `CELERY_TASK_ALWAYS_EAGER` explicitly.

This is useful for development because:
- The email send happens immediately.
- SMTP errors show up in the Django `runserver` terminal.

### Worker mode

If you disable eager mode, you must run a worker to process queued tasks.

## Admin

The accounts admin is configured to:

- Register the custom `accounts.User` model.
- Show key fields (role, verified, MFA, deleted).
- Edit the `accounts.Profile` inline on the user page.
- Show `accounts.PasswordHistory` as read-only.

## Troubleshooting

### “No email received”

- Make sure `.env` is loaded (use `py manage.py shell` and print `settings.EMAIL_HOST_USER`).
- If using Gmail, use an App Password.
- Check Gmail spam.

### “Redis connection refused”

- Start Redis on `localhost:6379`, OR
- In dev, the project will fall back to Django cache.

### “Verification link works in email but browser doesn’t verify”

The email link is a frontend link. The backend verification is:

- `POST /api/auth/verify-email/` with `uid` and `token`.

Your frontend (if/when you build it) should call that API endpoint.
