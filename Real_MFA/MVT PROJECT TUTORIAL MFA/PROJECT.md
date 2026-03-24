# MVT Real MFA Project Guide (How Everything Connects)

## 1. Goal
Build complete MFA web app in Django MVT without DRF, using secure layered architecture.

## 2. Project Wiring (High Level)

1. Browser sends request to URL.
2. URL maps to app view.
3. View calls form validation.
4. View or service updates models.
5. Signals trigger side workflows (profile, notifications, logs).
6. Template renders response.

## 3. How Apps Connect

- `accounts` is entry point for identity and session start.
- `otp` is second-factor gate before final login.
- `devices` stores trust and active session context.
- `notification` sends and tracks alerts.
- `audits_logs` records every critical event.

Typical login chain:

`accounts.views.login` -> password ok -> pending session -> `otp.views.verify` -> success -> `devices` session/trust update -> `audits_logs` insert -> optional `notification` alert.

## 4. File-Level Dependency Pattern

- `models.py` should depend only on Django and local constants.
- `forms.py` depends on models + validators.
- `views.py` depends on forms + services.
- `services.py` depends on models + infrastructure clients.
- `signals.py` should call services, not heavy raw logic.

## 5. Recommended Missing Pieces to Add

1. Dedicated `services/` layer per app.
2. Central `security.py` for policy values (lockout, OTP expiry, trust days).
3. Feature flags for fallback behavior.
4. Better exception classes (`RegistrationError`, `MFAError`, `NotificationError`).
5. Structured logging with request id and user id.

## 6. Advanced Concepts (Including DSA Thinking)

### 6.1 DSA/Algorithm Ideas in Security Flows

1. Sliding window rate limiter:
- Use deque/timestamp buckets per user/ip for precise throttling.

2. LRU for suspicious fingerprint cache:
- Keep recent device fingerprints in bounded memory store.

3. Priority queue for delayed retry tasks:
- Retry failed notifications using exponential backoff scheduling.

4. Set + hashmap combo for active session invalidation:
- O(1) lookup to revoke session tokens quickly.

5. Graph-style risk propagation:
- Model relationship between user, IP, device, location to detect anomaly clusters.

### 6.2 Data Modeling Optimizations

- Composite indexes on `(user, created_at)` and `(event_type, created_at)`.
- Partial indexes for active/unexpired records.
- Partition heavy audit tables by month for scale.

### 6.3 Concurrency and Atomicity

- Use `transaction.atomic` in registration/login critical paths.
- Keep side effects (email send) outside critical transaction where possible.
- Use idempotency keys for retry-safe operations.

## 7. Testing Plan (What to Cover)

1. Unit tests for forms and model methods.
2. Integration tests for register->verify->login->mfa.
3. Regression tests for known failures:
- JSON serialization issues
- unique provider id collisions
- broken transaction chain after side-effect failures

## 8. Deployment Layers

1. App (gunicorn)
2. DB (postgres)
3. Cache/queue (redis)
4. reverse proxy (nginx)
5. background worker (celery)

## 9. Production Readiness Checklist

- DEBUG False
- secure cookies true (with HTTPS)
- CSRF trusted origins configured
- secrets moved out of repository
- health checks + monitoring
- periodic backups
- alerts for auth anomalies

## 10. Learning Path Suggestion

1. Build accounts + templates first.
2. Add OTP flow.
3. Add device trust.
4. Add notifications and audit logs.
5. Add queue/workers.
6. Add deployment automation and observability.

This sequence gives understanding first, then scale.

## 11. Real Project Update Notes (March 2026)

### 11.1 Domain and Host Policy

For current deployment, align these values together:

- `ALLOWED_HOSTS=awaisamjad.engineer,www.awaisamjad.engineer,...`
- `CSRF_TRUSTED_ORIGINS=https://awaisamjad.engineer,https://www.awaisamjad.engineer`
- `CORS_ALLOWED_ORIGINS=https://awaisamjad.engineer,https://www.awaisamjad.engineer`

If origin lists do not match your public domain, forms and session-based auth flows may fail with CSRF errors.

### 11.2 Docker and Cloud Hostnames

- Inside Docker Compose network: use service names (`db`, `redis`) as hosts.
- In managed cloud DB/Redis: use provider hostname and numeric port.
- Never leave placeholder values like `<do_pg_port_numeric>` in env; startup will fail.

### 11.3 Registration/Notification Reliability

Known fixed failure pattern in this project:

1. Notification metadata included Python datetime object directly.
2. JSON field save raised serialization error.
3. Subsequent retry path could hit unique collision on provider message ID.

Current guidance:

- Convert metadata to JSON-safe structure before persistence.
- Ensure `provider_message_id` is always unique when creating notification records.

### 11.4 Admin Login Behavior

This codebase uses email verification checks in auth flow. For admin bootstrap:

- superuser creation should mark verified email by default, or
- manually mark verification status before first admin login.
