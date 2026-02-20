# Real_MFA Complete Deployment on DigitalOcean Droplet (Ubuntu 24.04)

## Your Droplet Info
- IP: `143.110.139.119`
- OS: Ubuntu 24.04.3 LTS
- RAM: Sufficient for 1-2 Django projects
- Root access: ✅ Available

---

## Phase 1: Initial Server Setup (Security + Dependencies)

### Step 1.1: Update system
```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

### Step 1.2: Create non-root user (best practice)
```bash
adduser realuser
# Enter password and details when prompted
usermod -aG sudo realuser
su - realuser
```

### Step 1.3: Configure SSH (security hardening)
```bash
# Generate SSH key on your LOCAL machine (not the droplet)
# On your Windows terminal:
# ssh-keygen -t ed25519 -C "your-email@example.com"
# Then add public key to droplet:

# On droplet as realuser:
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Paste your public key:
nano ~/.ssh/authorized_keys
# Ctrl+X, Y to save
chmod 600 ~/.ssh/authorized_keys
```

### Step 1.4: Disable password login (SSH key only)
```bash
sudo nano /etc/ssh/sshd_config
# Find and change:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes

sudo systemctl restart ssh
```

### Step 1.5: Enable firewall
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

---

## Phase 2: Install Core Dependencies

### Step 2.1: Install Python + pip + git
```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git curl wget
python3.11 --version
pip3 --version
```

### Step 2.2: Install PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib postgresql-client
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql --version
```

### Step 2.3: Install other system packages
```bash
sudo apt install -y nginx redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 2.4: Install supervisor (for process management)
```bash
sudo apt install -y supervisor
```

---

## Phase 3: PostgreSQL Database Setup

### Step 3.1: Create database and user
```bash
sudo -u postgres psql
# Inside psql terminal:

CREATE DATABASE real_mfa_db;
CREATE USER real_mfa_user WITH PASSWORD 'strong_password_here_123!@#';
ALTER ROLE real_mfa_user SET client_encoding TO 'utf8';
ALTER ROLE real_mfa_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE real_mfa_user SET default_transaction_deferrable TO on;
ALTER ROLE real_mfa_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO real_mfa_user;
\q
```

### Step 3.2: Verify connection
```bash
psql -U real_mfa_user -d real_mfa_db -h localhost -c "SELECT version();"
# Should show PostgreSQL version
```

---

## Phase 4: Clone and Setup Real_MFA Project

### Step 4.1: Clone repository
```bash
cd /home/realuser
git clone https://github.com/your-username/Real_MFA.git real_mfa
cd real_mfa/Real_MFA
```

### Step 4.2: Create Python virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Step 4.3: Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4.4: Create production .env file
```bash
nano .env
```

Paste this (update values):
```env
# Django Settings
SECRET_KEY=generate-a-strong-key-here-use-`python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
DEBUG=False
ALLOWED_HOSTS=143.110.139.119,your-domain.com,www.your-domain.com
ENVIRONMENT=production

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=real_mfa_db
DB_USER=real_mfa_user
DB_PASSWORD=strong_password_here_123!@#
DB_HOST=localhost
DB_PORT=5432

# Redis (Celery Broker)
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email Configuration (Gmail example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Frontend
FRONTEND_URL=https://your-domain.com

# Security
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 4.5: Run migrations
```bash
python manage.py migrate
```

### Step 4.6: Collect static files
```bash
python manage.py collectstatic --noinput
```

### Step 4.7: Create superuser
```bash
python manage.py createsuperuser
# Follow prompts
```

### Step 4.8: Test locally (optional)
```bash
python manage.py runserver 0.0.0.0:8000
# Visit http://143.110.139.119:8000 (Ctrl+C to stop)
```

---

## Phase 5: Gunicorn Setup (WSGI Application Server)

### Step 5.1: Install Gunicorn
```bash
source venv/bin/activate
pip install gunicorn
```

### Step 5.2: Create systemd service file
```bash
sudo nano /etc/systemd/system/real_mfa_gunicorn.service
```

Paste:
```ini
[Unit]
Description=Real_MFA Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=realuser
Group=www-data
WorkingDirectory=/home/realuser/real_mfa/Real_MFA
Environment="PATH=/home/realuser/real_mfa/venv/bin"
EnvironmentFile=/home/realuser/real_mfa/Real_MFA/.env
ExecStart=/home/realuser/real_mfa/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --bind unix:/run/gunicorn_real_mfa.sock \
    --timeout 60 \
    --log-level info \
    Real_MFA.wsgi:application

[Install]
WantedBy=multi-user.target
```

Save and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl start real_mfa_gunicorn
sudo systemctl enable real_mfa_gunicorn
sudo systemctl status real_mfa_gunicorn
```

---

## Phase 6: Celery Setup (Background Tasks)

### Step 6.1: Create Celery worker service
```bash
sudo nano /etc/systemd/system/real_mfa_celery.service
```

Paste:
```ini
[Unit]
Description=Real_MFA Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=realuser
Group=www-data
WorkingDirectory=/home/realuser/real_mfa/Real_MFA
Environment="PATH=/home/realuser/real_mfa/venv/bin"
EnvironmentFile=/home/realuser/real_mfa/Real_MFA/.env
ExecStart=/home/realuser/real_mfa/venv/bin/celery -A Real_MFA worker \
    --loglevel=info \
    --logfile=/var/log/real_mfa_celery_worker.log \
    --pidfile=/run/celery_worker.pid

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl start real_mfa_celery
sudo systemctl enable real_mfa_celery
sudo systemctl status real_mfa_celery
```

### Step 6.2: Create Celery beat service (scheduler)
```bash
sudo nano /etc/systemd/system/real_mfa_celery_beat.service
```

Paste:
```ini
[Unit]
Description=Real_MFA Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=realuser
Group=www-data
WorkingDirectory=/home/realuser/real_mfa/Real_MFA
Environment="PATH=/home/realuser/real_mfa/venv/bin"
EnvironmentFile=/home/realuser/real_mfa/Real_MFA/.env
ExecStart=/home/realuser/real_mfa/venv/bin/celery -A Real_MFA beat \
    --loglevel=info \
    --logfile=/var/log/real_mfa_celery_beat.log \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl start real_mfa_celery_beat
sudo systemctl enable real_mfa_celery_beat
sudo systemctl status real_mfa_celery_beat
```

---

## Phase 7: Nginx Reverse Proxy Setup

### Step 7.1: Create Nginx config
```bash
sudo nano /etc/nginx/sites-available/real_mfa
```

Paste (replace `your-domain.com`):
```nginx
upstream real_mfa_app {
    server unix:/run/gunicorn_real_mfa.sock fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name 143.110.139.119 your-domain.com www.your-domain.com;
    client_max_body_size 20M;

    location / {
        proxy_pass http://real_mfa_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/realuser/real_mfa/Real_MFA/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/realuser/real_mfa/Real_MFA/media/;
        expires 7d;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/real_mfa /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Step 7.2: Test HTTP access
```bash
# From your local machine:
curl http://143.110.139.119
# Or visit http://143.110.139.119 in browser
```

---

## Phase 8: SSL/HTTPS Setup (Let's Encrypt)

### Step 8.1: Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Step 8.2: Get SSL certificate (replace your-domain.com)
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
# Follow prompts, agree to terms
```

### Step 8.3: Auto-renewal
```bash
sudo systemctl enable certbot.timer
sudo certbot renew --dry-run
```

### Step 8.4: Test HTTPS
```bash
# Visit https://your-domain.com in browser
# Should show padlock (secure)
```

---

## Phase 9: Monitoring & Logs

### Check service status:
```bash
sudo systemctl status real_mfa_gunicorn
sudo systemctl status real_mfa_celery
sudo systemctl status real_mfa_celery_beat
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
```

### View logs:
```bash
# Gunicorn logs
sudo tail -f /var/log/syslog | grep gunicorn

# Celery logs
sudo tail -f /var/log/real_mfa_celery_worker.log
sudo tail -f /var/log/real_mfa_celery_beat.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Django logs (if configured)
tail -f /home/realuser/real_mfa/Real_MFA/logs/django.log
```

---

## Phase 10: Backup & Maintenance

### Database backup:
```bash
sudo -u postgres pg_dump real_mfa_db > /home/realuser/backup_$(date +%Y%m%d).sql
```

### Database restore:
```bash
sudo -u postgres psql real_mfa_db < backup_20250805.sql
```

### Update code:
```bash
cd /home/realuser/real_mfa
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart real_mfa_gunicorn
```

---

## Troubleshooting

### Gunicorn fails to start
```bash
sudo systemctl status real_mfa_gunicorn
# Check /var/log/syslog
# Validate .env file exists and readable
sudo cat /home/realuser/real_mfa/Real_MFA/.env
```

### Database connection error
```bash
psql -U real_mfa_user -d real_mfa_db -h localhost
# If fails, check PostgreSQL is running:
sudo systemctl status postgresql
```

### Celery worker not processing tasks
```bash
# Check Redis is running
redis-cli ping  # Should respond with PONG

# Check Celery can connect
source /home/realuser/real_mfa/venv/bin/activate
celery -A Real_MFA inspect active
```

### 502 Bad Gateway from Nginx
```bash
# Check Gunicorn socket exists
ls -la /run/gunicorn_real_mfa.sock

# Restart Gunicorn
sudo systemctl restart real_mfa_gunicorn
```

### Static files not loading
```bash
# Recollect static files
cd /home/realuser/real_mfa/Real_MFA
source venv/bin/activate
python manage.py collectstatic --noinput --clear
sudo systemctl restart real_mfa_gunicorn
```

---

## Quick Deployment Checklist

- [ ] System updated
- [ ] Non-root user created
- [ ] SSH key-only auth enabled
- [ ] Firewall configured
- [ ] PostgreSQL installed + database created
- [ ] Redis installed + running
- [ ] Real_MFA cloned + .env created
- [ ] Migrations run
- [ ] Static files collected
- [ ] Gunicorn service created + enabled
- [ ] Celery worker + beat services created
- [ ] Nginx configured + tested
- [ ] SSL certificate installed
- [ ] All services running (systemctl status)
- [ ] Domain pointing to IP / A record set
- [ ] visited https://your-domain.com successfully

---

## Next Steps (For 2nd Project)

To deploy another Django project:
1. Create separate database + user in PostgreSQL
2. Clone new project repo
3. Create separate venv + .env
4. Create separate `_gunicorn.service`, `_celery.service` files
5. Create separate Nginx config + SSL
6. Enable all services

Same droplet can handle 2-3 medium projects!

---

## Production Security Reminders

- Never commit `.env` to git
- Use strong passwords everywhere
- Keep system updated: `sudo apt update && sudo apt upgrade -y`
- Regular backups of PostgreSQL
- Monitor logs weekly
- Rotate secrets every 60-90 days
- Limit superuser access
- Use HTTPS everywhere

---

## Support Commands (Copy-paste ready)

```bash
# SSH to droplet (from local machine)
ssh realuser@143.110.139.119

# Restart all services
sudo systemctl restart real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx

# Check all running
sudo systemctl status real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx postgresql redis-server

# View recent errors
sudo journalctl -u real_mfa_gunicorn -n 50
sudo journalctl -u real_mfa_celery -n 50

# Deep DB check
sudo -u postgres psql -d real_mfa_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
```

Done! Real_MFA is now production-ready on your Digital Ocean droplet.
