# Production Deployment Checklist for GitHub

Before pushing to GitHub and deploying to Ubuntu/DigitalOcean, complete this checklist:

## Code Quality

- [ ] No debug break points left in code
- [ ] No `print()` statements (use logging instead)
- [ ] No hardcoded credentials in code
- [ ] All imports are used and organized
- [ ] Code follows PEP 8 standards

## Security & Environment

- [ ] `.env` file is in `.gitignore`
- [ ] `.env.example` exists with placeholder values
- [ ] `SECRET_KEY` will be set via environment variable
- [ ] No sensitive data in git history
- [ ] Database password will be set via environment variable
- [ ] Email credentials will be set via environment variable

## Database

- [ ] All migrations created and tested
- [ ] Migration files are in git (don't .gitignore migrations)
- [ ] Database queries optimized
- [ ] No N+1 queries
- [ ] Indexes set for frequently queried fields

## Django Settings

- [ ] `DEBUG = False` in production (controlled by `ENVIRONMENT`)
- [ ] `ALLOWED_HOSTS` configured via environment variable
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] `CORS_ALLOWED_ORIGINS` configured properly
- [ ] `SECURE_SSL_REDIRECT = True` (production-only)
- [ ] `SESSION_COOKIE_SECURE = True` (production-only)
- [ ] `CSRF_COOKIE_SECURE = True` (production-only)
- [ ] `HSTS_SECONDS = 31536000` (production-only)
- [ ] Static files configured with `STATIC_ROOT`
- [ ] Media files configured with `MEDIA_ROOT`

## Dependencies

- [ ] `requirements.txt` is up to date
- [ ] Only production dependencies listed
- [ ] Python 3.11+ specified in documentation
- [ ] PostgreSQL driver (psycopg2) included
- [ ] Gunicorn included for production
- [ ] Celery and Redis packages included
- [ ] No dev dependencies in production file

## Celery Configuration

- [ ] Redis configuration set
- [ ] Celery broker and result backend configured
- [ ] Celery beat schedule defined
- [ ] Task timeouts configured
- [ ] Dead letter queue configured
- [ ] Retry policies set

## API & CORS

- [ ] API endpoints secured (authentication required)
- [ ] CORS headers properly set
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] API versioning if needed

## Logging

- [ ] Logging configured with file rotation
- [ ] Log level set to INFO (not DEBUG) in production
- [ ] Sensitive data not logged (passwords, tokens)
- [ ] Async logging configured for production

## Email

- [ ] Email backend configured
- [ ] Email templates created
- [ ] Test email functionality
- [ ] Email variables will be set via environment

## Static & Media Files

- [ ] Static files can be collected
- [ ] Media directory is created
- [ ] Static files are not in git (only serve from nginx)
- [ ] `.collectstatic` runs without errors

## Testing

- [ ] Unit tests pass: `python manage.py test`
- [ ] All models have tests
- [ ] All API endpoints have tests
- [ ] Authentication tests included
- [ ] Integration tests for critical flows

## Documentation

- [ ] README.md has setup instructions
- [ ] DEPLOYMENT.md has Ubuntu setup instructions
- [ ] .env.example has all needed variables
- [ ] Installation steps documented
- [ ] Environment variables documented

## Files to Commit

Commit these files to GitHub:
- [ ] `settings.py` (with environment-aware settings)
- [ ] `celery.py` (with production config)
- [ ] `wsgi.py` (updated for production)
- [ ] `urls.py` (with media file serving)
- [ ] `requirements.txt` (up to date)
- [ ] `.env.example` (no secrets, just templates)
- [ ] `.gitignore` (proper Python/Django rules)
- [ ] `manage.py`
- [ ] All app code
- [ ] All migrations
- [ ] Configuration files in `config/` directory
- [ ] Documentation in `docs/` directory

## Files NOT to Commit

- [ ] `.env` (keep locally, use .env.example instead)
- [ ] `db.sqlite3` (or any local database)
- [ ] `venv/` or virtual environment
- [ ] `__pycache__/`
- [ ] `*.pyc`
- [ ] `logs/`
- [ ] `media/`
- [ ] `staticfiles/`

## Ubuntu/DigitalOcean Specific

- [ ] PostgreSQL configuration file ready
- [ ] Nginx configuration file ready in `config/`
- [ ] Gunicorn systemd service file ready
- [ ] Celery systemd service files ready
- [ ] Backup script ready
- [ ] Monitor script ready
- [ ] Deploy script ready

## Before Pushing to GitHub

```bash
# Check for secrets
git log --all -S "password" --oneline
git log --all -S "secret" --oneline
git log --all -S "key" --oneline

# Verify .gitignore
git status --porcelain | head -20

# Test locally
python manage.py collectstatic --noinput --dry-run
python manage.py check --deploy
python manage.py test

# Check for large files
find . -size +10M | grep -v ".git/"

# Final check before push
git diff --cached  # Review all changes
```

## Ubuntu Deployment Commands

Once pushed to GitHub and on Ubuntu:

```bash
# 1. Clone repository
git clone https://github.com/your-username/Real_MFA.git
cd Real_MFA

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
nano .env  # Edit with your values

# 5. Setup database
sudo -u postgres psql
CREATE DATABASE real_mfa_db;
CREATE USER real_mfa_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO real_mfa_user;

# 6. Run migrations
cd Real_MFA
python manage.py migrate

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Copy service files
sudo cp config/real_mfa_gunicorn.service /etc/systemd/system/
sudo cp config/real_mfa_celery.service /etc/systemd/system/
sudo cp config/real_mfa_celery_beat.service /etc/systemd/system/
sudo cp config/nginx_real_mfa.conf /etc/nginx/sites-available/

# 9. Setup services
sudo systemctl daemon-reload
sudo systemctl enable real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat
sudo systemctl start real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat

# 10. Setup Nginx
sudo systemctl reload nginx

# 11. Get SSL certificate
sudo certbot --nginx -d your-domain.com

# 12. Verify
bash config/monitor.sh
```

## Ready to Deploy!

Once all checkboxes are checked:

```bash
# Commit everything
git add .
git commit -m "Production-ready deployment"
git push origin main

# Read deployment guide
# docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md
```

---

**Deployment Ready:** [ ] Yes, all items checked!
