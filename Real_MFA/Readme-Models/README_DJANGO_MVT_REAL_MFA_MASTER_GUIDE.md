# Django MVT Real MFA Master Guide (Without DRF)

## 1. What You Are Building

This guide teaches how to build a production-style **Real MFA** project in plain Django using:

- Models
- Views
- Templates
- Forms
- Sessions
- Middleware
- Signals
- Celery (optional for async emails)
- PostgreSQL + Redis

No Django REST Framework is required in this version.

The final target is a web app where users can:

- Register with email/password
- Verify email
- Login with password
- Complete second factor (email OTP or TOTP)
- Manage trusted devices
- View account activity logs
- Reset password securely

This document is written as a practical blueprint. You can implement it app-by-app in your existing workspace.

---

## 2. MVT vs DRF for Learning

Why start with MVT first:

1. You understand the complete request lifecycle from browser to database.
2. You learn Django authentication deeply.
3. You can debug security flows with less abstraction.
4. DRF becomes easier later because business logic is already separated.

Mental model:

- Model: Data + constraints + behavior
- View: Request/response orchestration
- Template: Presentation
- Form: Input validation layer for HTML forms

---

## 3. Prerequisites

- Python 3.11+
- Django 4.2+
- PostgreSQL 14+
- Redis 6+
- Virtual environment
- Basic HTML/CSS

Optional:

- Celery + Celery Beat
- Docker + Docker Compose
- Nginx + Gunicorn

---

## 4. High-Level Architecture

Apps you should create:

1. `accounts` -> User model, registration/login/profile
2. `otp` -> OTP and TOTP logic
3. `devices` -> Device fingerprint and trust
4. `notification` -> Email notifications
5. `audits_logs` -> Security/audit events

Core MFA flow:

1. User submits username/email + password.
2. If password valid, system checks MFA method.
3. If email OTP: send OTP and store pending auth state in session.
4. If TOTP: verify TOTP code.
5. If success: finalize login and create audit log.

---

## 5. Initial Project Bootstrap

### 5.1 Create project

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install django psycopg2-binary python-dotenv redis celery pyotp qrcode pillow whitenoise
django-admin startproject Real_MFA .
python manage.py startapp accounts
python manage.py startapp otp
python manage.py startapp devices
python manage.py startapp notification
python manage.py startapp audits_logs
```

### 5.2 Core folder structure

```text
Real_MFA/
  manage.py
  .env
  requirements.txt
  Real_MFA/
    settings.py
    urls.py
    wsgi.py
    asgi.py
    middleware.py
  accounts/
    models.py
    forms.py
    views.py
    urls.py
    admin.py
    signals.py
    templates/accounts/
  otp/
    models.py
    forms.py
    views.py
    urls.py
    utils.py
    templates/otp/
  devices/
    models.py
    views.py
    urls.py
    utils.py
    templates/devices/
  notification/
    models.py
    services.py
    templates/notification/email/
  audits_logs/
    models.py
    admin.py
  templates/
    base.html
    home.html
  static/
    css/
    js/
```

---

## 6. Environment Variables Design

Use `.env` for local/dev and production secrets via host env.

Example:

```env
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=django.db.backends.postgresql
DB_NAME=real_mfa_db
DB_USER=real_mfa_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000
CORS_ALLOWED_ORIGINS=http://127.0.0.1:8000
```

---

## 7. Settings File Blueprint

In `settings.py`:

1. Load `.env` with `python-dotenv`.
2. Set custom user model early.
3. Add all apps.
4. Add template dir and static config.
5. Configure session security.
6. Configure email and cache.

Essential parts:

```python
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "otp",
    "devices",
    "notification",
    "audits_logs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT") or str(BASE_DIR / "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT") or str(BASE_DIR / "media")
```

Session hardening (production):

```python
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

---

## 8. Database Modeling Strategy

### 8.1 Accounts models

- `User` (custom)
- `Profile`
- `PasswordHistory`

Recommended `User` fields:

- `id` UUID
- `email` unique
- `username` unique
- `role`
- `email_verified`
- `mfa_enabled`
- `mfa_method`
- `failed_login_attempts`
- `account_locked_until`
- timestamps

### 8.2 OTP models

- `EmailOTP`
- `TOTPDevice`
- `BackupCode`

### 8.3 Devices models

- `Device`
- `TrustedDevice`
- `Session`

### 8.4 Notification models

- `EmailNotification`
- `NotificationPreference`
- `NotificationLog`

### 8.5 Audit models

- `AuditLog`

---

## 9. Custom User Model (Critical)

Create custom user on day one.

`accounts/models.py` shape:

```python
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    mfa_method = models.CharField(max_length=20, default="email")
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
```

Manager should support `create_user` and `create_superuser`.

---

## 10. Forms Layer (Without DRF)

Build robust Django Forms:

1. `RegisterForm`
2. `LoginForm`
3. `EmailOTPForm`
4. `TOTPForm`
5. `ProfileUpdateForm`
6. `PasswordChangeForm`
7. `ForgotPasswordForm`
8. `ResetPasswordForm`

Why forms are important:

- Central validation
- Cleaner templates
- Better error rendering
- Lower controller complexity

---

## 11. URL Design for MVT

Recommended routes:

- `/` home
- `/auth/register/`
- `/auth/login/`
- `/auth/logout/`
- `/auth/verify-email/`
- `/auth/mfa/verify/`
- `/auth/password/forgot/`
- `/auth/password/reset/<token>/`
- `/dashboard/`
- `/devices/`
- `/devices/trust/<uuid>/`
- `/security/activity/`

Keep app-level URLs in each app and include in project `urls.py`.

---

## 12. Registration Flow (Template Version)

Flow:

1. GET register page with form.
2. POST register data.
3. Validate unique email/username.
4. Create user with `is_active=True`, `email_verified=False`.
5. Create profile.
6. Generate email verification token.
7. Send verification email.
8. Redirect to "check your inbox" page.

View sketch:

```python
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = False
            user.save()
            Profile.objects.get_or_create(user=user)
            send_verification_email(user)
            messages.success(request, "Registration successful. Verify your email.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})
```

---

## 13. Email Verification Flow

Use Django token generator + UID.

Steps:

1. Build URL with uid + token.
2. Send email with link.
3. In verify view, decode uid and validate token.
4. Mark `email_verified=True`.

Important checks:

- Expiry checks
- Single-use behavior
- Log all attempts in audit table

---

## 14. Login + MFA State Machine

### 14.1 Password phase

1. Validate credentials.
2. Check lockout policy.
3. If no MFA enabled -> login directly.
4. If MFA enabled -> store pending user in session and redirect to mfa verify page.

Session keys:

- `pending_user_id`
- `pending_mfa_method`
- `pending_device_fingerprint`
- `pending_expires_at`

### 14.2 MFA phase

- For Email OTP:
  - generate OTP
  - send email
  - verify code + expiry + attempts
- For TOTP:
  - verify via pyotp
- On success:
  - finalize login with `login(request, user)`
  - create session/device/audit records

---

## 15. OTP Models and Logic

`otp/models.py` example concepts:

- `otp_code`
- `purpose` (`login`, `password_reset`, `device_verification`)
- `expires_at`
- `attempt_count`
- `max_attempts`
- `is_used`

Validation rule:

$$
\text{valid OTP} = (\text{not used}) \land (\text{now} < \text{expires\_at}) \land (\text{attempts} < \text{max})
$$

---

## 16. TOTP Setup (Authenticator App)

1. Generate secret with `pyotp.random_base32()`.
2. Store secret encrypted/hashed policy-based.
3. Build provisioning URI.
4. Render QR in template.
5. User scans and submits first TOTP code.
6. Verify and enable `mfa_enabled=True, mfa_method='totp'`.

---

## 17. Device Tracking and Trust

Collect lightweight device data from request:

- user agent
- ip
- fingerprint hash (optional JS-based)
- browser/os parsed

On first verified login:

- create device record
- optionally trust for N days
- allow "remember this device"

Device trust should expire and be revocable.

---

## 18. Security and Lockout Policy

Implement login defense:

- Max failed attempts: e.g. 5
- Lock duration: e.g. 30 min
- Reset on successful login

Pseudo:

```python
if user.failed_login_attempts >= 5:
    user.account_locked_until = now + timedelta(minutes=30)
```

Add per-IP throttling for login/register via cache.

---

## 19. Notification Design

For each security event send notification:

- new device login
- password change
- MFA enabled/disabled
- suspicious login

Persist notification records for audit.

Very important DB rule:

- `provider_message_id` unique field should never be empty for multiple rows.
- Always generate one when creating records if external provider does not return one.

---

## 20. Audit Logging

Create `AuditLog` with:

- user
- action
- ip
- user_agent
- metadata JSON
- created_at

Log these events:

- register success/failure
- email verify success/failure
- login success/failure
- mfa success/failure
- password reset start/complete
- device trust added/removed

---

## 21. Templates Structure

Recommended:

```text
templates/
  base.html
  includes/
    navbar.html
    messages.html
  accounts/
    register.html
    login.html
    verify_email_sent.html
    verify_email_result.html
  otp/
    verify_otp.html
    setup_totp.html
  devices/
    list.html
    detail.html
    trust_confirm.html
  security/
    activity.html
```

`base.html` should include:

- csrf token meta
- messages block
- nav links based on auth state

---

## 22. Frontend Patterns for Forms

For each form template:

1. show field errors inline
2. show non-field errors at top
3. disable submit button during post
4. include CSRF token
5. maintain accessibility labels

---

## 23. Middleware Ideas

Custom middleware you can add later:

- `LastActivityMiddleware`
- `IPCaptureMiddleware`
- `SecurityHeadersMiddleware`

Example use:

- update `user.last_activity` for authenticated requests
- centralize client IP extraction

---

## 24. Service Layer Pattern

To keep views clean, create services:

- `accounts/services/auth_service.py`
- `otp/services/otp_service.py`
- `notification/services/email_service.py`
- `devices/services/device_service.py`

Views call services; services hold business logic.

---

## 25. Management Commands You Should Build

1. `cleanup_expired_otps`
2. `cleanup_expired_sessions`
3. `cleanup_unverified_accounts`
4. `rotate_audit_logs`

Run with cron/Celery beat.

---

## 26. Celery Integration (Optional Early, Useful Later)

Use Celery to send emails asynchronously.

Core tasks:

- send verification email
- send OTP email
- send security alert

Fallback strategy:

- If task queue unavailable, log warning and continue flow gracefully.

---

## 27. Static and Media Handling

For single-server deployment:

- WhiteNoise for static
- local filesystem for media

For scale:

- S3/Spaces for media
- CDN for static

---

## 28. Testing Strategy (Must-Have)

### Unit tests

- user manager
- forms validation
- OTP generation and expiry
- lockout logic

### Integration tests

- register -> verify email -> login -> mfa verify
- failed login attempts -> lockout
- password reset full flow

### Security tests

- CSRF checks
- brute-force protection
- token tampering

---

## 29. Recommended Incremental Build Plan

Phase 1 (foundation):

1. custom user model
2. registration/login templates
3. email verification

Phase 2 (MFA core):

1. email OTP
2. TOTP setup/verify
3. session pending state

Phase 3 (security hardening):

1. device trust
2. audit logs
3. lockout + rate limiting

Phase 4 (production readiness):

1. notifications
2. celery tasks
3. docker + nginx + gunicorn

---

## 30. Dockerized MVT Deployment Approach

Services:

- web (django+gunicorn)
- db (postgres)
- redis
- nginx
- celery worker/beat (optional)

At startup:

1. wait db/redis
2. migrate
3. collectstatic
4. start gunicorn

---

## 31. Common Mistakes and Fixes

1. **Custom user added too late**
- Fix: define from start and migrate fresh.

2. **500 on register due to side effects**
- Fix: isolate side effects and wrap failures.

3. **Non-serializable JSON in metadata**
- Fix: normalize metadata with `DjangoJSONEncoder`.

4. **Unique provider message id collisions**
- Fix: always assign generated unique id.

5. **Local DB connection refused**
- Fix: ensure PostgreSQL running or use Docker db port mapping.

---

## 32. File-by-File Starter Checklist

### accounts/

- `models.py` custom user/profile/password history
- `forms.py` register/login/profile/password forms
- `views.py` auth and dashboard views
- `urls.py` auth routes
- `signals.py` profile auto-create, optional email events
- `admin.py` custom admin for user/profile

### otp/

- `models.py` OTP + TOTP models
- `forms.py` otp submit forms
- `views.py` setup/verify views
- `urls.py`
- `utils.py` generator + verifier helpers

### devices/

- `models.py` device/session models
- `views.py` list/trust/remove
- `urls.py`
- `utils.py` parser helpers

### notification/

- `models.py` email/sms/log preferences
- `services.py` notification sender wrappers
- email templates

### audits_logs/

- `models.py` audit log
- `admin.py` readonly listing

---

## 33. Example Register Template

```html
{% extends "base.html" %}
{% block content %}
<h1>Create account</h1>
<form method="post">
  {% csrf_token %}
  {{ form.non_field_errors }}
  <div>{{ form.username.label_tag }} {{ form.username }} {{ form.username.errors }}</div>
  <div>{{ form.email.label_tag }} {{ form.email }} {{ form.email.errors }}</div>
  <div>{{ form.password1.label_tag }} {{ form.password1 }} {{ form.password1.errors }}</div>
  <div>{{ form.password2.label_tag }} {{ form.password2 }} {{ form.password2.errors }}</div>
  <button type="submit">Register</button>
</form>
{% endblock %}
```

---

## 34. Example Login + MFA Redirect Logic

```python
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.mfa_enabled:
                request.session["pending_user_id"] = str(user.id)
                request.session["pending_mfa_method"] = user.mfa_method
                return redirect("otp:verify")
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})
```

---

## 35. Example OTP Verify View

```python
def verify_otp_view(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return redirect("accounts:login")

    user = get_object_or_404(User, id=user_id)
    form = EmailOTPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
        if validate_email_otp(user, code):
            login(request, user)
            request.session.pop("pending_user_id", None)
            request.session.pop("pending_mfa_method", None)
            return redirect("accounts:dashboard")
        form.add_error("code", "Invalid or expired OTP")

    return render(request, "otp/verify_otp.html", {"form": form})
```

---

## 36. Production Hardening Checklist

1. `DEBUG=False`
2. strong `SECRET_KEY`
3. HTTPS enabled
4. secure cookies enabled
5. CSRF trusted origins correct
6. email credentials from env only
7. rotate leaked credentials immediately
8. database backups enabled
9. audit logs monitored
10. rate limits enabled

---

## 37. Migration and Data Safety

Before deploy:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check --deploy
```

Take backup before schema changes in production.

---

## 38. Dev Workflow (Daily)

1. Pull latest code
2. Activate venv
3. Run db/redis (docker or local)
4. Migrate
5. Run server
6. Test register/login/mfa
7. Run tests before push

---

## 39. Suggested Learning Order (Practical)

Week 1:

- custom user
- forms
- template auth

Week 2:

- email verification
- login lockout

Week 3:

- email OTP MFA
- TOTP setup

Week 4:

- devices + sessions
- audit + notifications
- production deployment

---

## 40. Full Build Checklist (Copy/Paste)

- [ ] Create project/apps
- [ ] Configure settings and env loading
- [ ] Implement custom user model
- [ ] Run initial migrations
- [ ] Build registration form + view + template
- [ ] Build email verification flow
- [ ] Build login flow
- [ ] Add lockout and failed attempts
- [ ] Build email OTP flow
- [ ] Build TOTP setup/verify
- [ ] Add device model and tracking
- [ ] Add trusted device UI
- [ ] Add session model and revoke flow
- [ ] Add audit logging
- [ ] Add notification records
- [ ] Add celery tasks for emails
- [ ] Add tests
- [ ] Add Docker and deploy

---

## 41. Minimal Command Cheatsheet

```bash
# local
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# docker
docker compose up -d --build
docker compose logs -f web

# deploy image
docker build -t yourhub/real_mfa:prod-v1 .
docker push yourhub/real_mfa:prod-v1
```

---

## 42. What to Convert to DRF Later

When you are ready:

1. Keep same models
2. Move form logic into serializers
3. Keep service layer unchanged
4. Add token/JWT endpoints
5. Add API permissions

This means your MVT foundation is not wasted.

---

## 43. Security Note You Must Follow

Never commit real secrets in git:

- DB password
- Redis password
- SMTP app password
- Django secret key

If leaked once, rotate immediately.

---

## 44. Final Guidance

If your goal is mastery, build this in layers:

1. Make it work
2. Make it secure
3. Make it observable (logs/audits)
4. Make it scalable (queues/cache)

Do not jump directly to advanced architecture before you can manually trace one login request end-to-end.

---

## 45. Next Suggested Deliverables

You can now ask for these one by one:

1. Full starter code for `accounts/models.py` (template version)
2. Full `RegisterForm`, `LoginForm`, `EmailOTPForm`
3. Full register/login/mfa views + urls
4. Template pack (`base`, `register`, `login`, `otp_verify`)
5. Device trust implementation
6. Audit logging middleware

This way you build the project with understanding, not copy-paste only.
