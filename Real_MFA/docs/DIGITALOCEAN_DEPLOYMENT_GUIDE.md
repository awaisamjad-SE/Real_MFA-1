# Real_MFA Deployment Guide on DigitalOcean

## Goal
Deploy Real_MFA in production on DigitalOcean with:
- Django API
- Gunicorn
- Celery worker + Celery beat
- Redis
- PostgreSQL (Managed Database)
- Nginx reverse proxy
- HTTPS via Let's Encrypt

This guide gives two options:
1. App Platform (managed, easiest)
2. Droplet + Docker Compose (full control)

---

## Prerequisites
- DigitalOcean account
- Domain name (recommended)
- Real_MFA source code in GitHub/GitLab
- Docker + Docker Compose (for local test)
- Basic Linux command knowledge

---

## Architecture (Recommended)
- App/API: Django + Gunicorn on Droplet or App Platform
- Worker: Celery worker process
- Scheduler: Celery beat process
- Cache/Broker: Redis
- DB: DigitalOcean Managed PostgreSQL
- Edge: Nginx + SSL

---

## Option A — Deploy on DigitalOcean App Platform (Quickest)

## Step 1: Prepare environment variables
Create production env values:
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=your-domain.com,www.your-domain.com`
- `DATABASE_URL=postgresql://...` (from DigitalOcean Managed DB)
- `CELERY_BROKER_URL=redis://...`
- `CELERY_RESULT_BACKEND=redis://...`
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS`
- `FRONTEND_URL=https://your-frontend-domain.com`

## Step 2: Create managed services
In DigitalOcean:
1. Create Managed PostgreSQL cluster.
2. Create Managed Redis cluster (or use same VPC Redis service).
3. Copy connection strings.

## Step 3: App Platform setup
1. Go to App Platform -> Create App.
2. Connect repository.
3. Configure components:
   - Web service: Django app (Gunicorn)
   - Worker service: Celery worker
   - Worker service: Celery beat
4. Set build/run commands:
   - Build: `pip install -r requirements.txt`
   - Web run: `python manage.py migrate ; gunicorn Real_MFA.wsgi:application --bind 0.0.0.0:$PORT`
   - Worker run: `celery -A Real_MFA worker -l info`
   - Beat run: `celery -A Real_MFA beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
5. Add all environment variables.
6. Deploy.

## Step 4: Domain and SSL
1. Attach custom domain in App Platform.
2. DigitalOcean provisions SSL automatically.
3. Verify API over HTTPS.

## Step 5: Health check endpoint
Add/confirm simple health endpoint (example `/health/`) for uptime checks.

---

## Option B — Deploy on Droplet + Docker Compose (Full Control)

## Step 1: Create droplet
- Ubuntu 22.04 LTS
- Minimum: 2 vCPU, 4 GB RAM (better for Celery + API)
- SSH key authentication enabled

## Step 2: Install dependencies on droplet
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release nginx

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Docker Compose plugin
sudo apt install -y docker-compose-plugin
```
Re-login after adding user to docker group.

## Step 3: Clone project
```bash
git clone <your-repo-url> real_mfa
cd real_mfa/Real_MFA
```

## Step 4: Production .env
Create `.env` in project root (same folder as `manage.py`):
```env
SECRET_KEY=change-to-strong-random-value
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

DB_NAME=defaultdb
DB_USER=doadmin
DB_PASSWORD=your-db-password
DB_HOST=your-managed-db-host
DB_PORT=25060

DATABASE_URL=postgresql://doadmin:your-db-password@your-managed-db-host:25060/defaultdb?sslmode=require

CELERY_BROKER_URL=redis://default:your-redis-password@your-managed-redis-host:25061/0
CELERY_RESULT_BACKEND=redis://default:your-redis-password@your-managed-redis-host:25061/0

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

FRONTEND_URL=https://your-frontend-domain.com
```

## Step 5: Dockerfile (example)
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
```

## Step 6: docker-compose.yml (production pattern)
```yaml
services:
  web:
    build: .
    command: sh -c "python manage.py migrate && gunicorn Real_MFA.wsgi:application --bind 0.0.0.0:8000 --workers 3"
    env_file:
      - .env
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    restart: always

  celery_worker:
    build: .
    command: celery -A Real_MFA worker -l info
    env_file:
      - .env
    volumes:
      - .:/app
    restart: always

  celery_beat:
    build: .
    command: celery -A Real_MFA beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file:
      - .env
    volumes:
      - .:/app
    restart: always
```

## Step 7: Start services
```bash
docker compose up -d --build
docker compose ps
```

## Step 8: Configure Nginx reverse proxy
Create Nginx site:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/real_mfa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 9: SSL with Let's Encrypt
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Step 10: Django production settings checklist
Ensure in settings:
- `DEBUG = False`
- `ALLOWED_HOSTS` includes domain
- `CSRF_TRUSTED_ORIGINS` includes `https://your-domain.com`
- Secure cookie settings enabled
- CORS configured for frontend domain only

---

## DigitalOcean Managed Database Notes
- Use SSL required mode for PostgreSQL.
- Add droplet/app to trusted sources in DB firewall settings.
- Use pooled connections if high traffic.

---

## DigitalOcean Managed Redis Notes
- Use private networking where possible.
- Keep Redis password secret.
- Restrict inbound access.

---

## CI/CD (Recommended)
- GitHub Actions pipeline:
  - Run tests
  - Build image
  - Push image to registry
  - SSH deploy to droplet (or App Platform auto deploy)

---

## Backups and Recovery
- Enable automated backups for Managed PostgreSQL.
- Schedule DB snapshot exports.
- Keep `.env` secrets backed in a secure vault.
- Test restore procedure monthly.

---

## Monitoring
- Application logs: `docker compose logs -f web`
- Worker logs: `docker compose logs -f celery_worker`
- Nginx logs: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- Uptime checks: `/health/` endpoint

---

## Security Hardening Checklist
- SSH key only (disable password auth)
- UFW firewall open only 22, 80, 443
- Fail2ban enabled
- Keep OS patched
- Use least-privilege DB user
- Rotate secrets every 60–90 days
- Restrict CORS/CSRF origins strictly

---

## Quick Deploy Commands (Droplet)
```bash
cd ~/real_mfa/Real_MFA
docker compose up -d --build
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check --deploy
```

---

## Troubleshooting

## App not starting
- Check env vars: `docker compose config`
- Check logs: `docker compose logs -f web`

## Celery not processing tasks
- Validate Redis URL and connectivity
- Check worker logs

## DB connection error
- Confirm trusted sources in DigitalOcean DB
- Confirm `sslmode=require`
- Verify credentials and host/port

## 502 from Nginx
- Ensure Gunicorn container running on `127.0.0.1:8000`
- Recheck Nginx proxy config and restart Nginx

---

## Final Recommendation
For quickest stable launch: use App Platform + Managed Postgres + Managed Redis.
For maximum control/cost optimization: use Droplet + Docker Compose + Nginx + managed data services.
