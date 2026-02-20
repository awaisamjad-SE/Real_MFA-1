## Real_MFA - Production Deployment for Ubuntu/DigitalOcean

Read the complete setup guide: [DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md](docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md)

### Quick Start

1. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Setup Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Database Setup** (PostgreSQL on Ubuntu)
   ```bash
   # Create PostgreSQL user and database
   sudo -u postgres psql
   CREATE DATABASE real_mfa_db;
   CREATE USER real_mfa_user WITH PASSWORD 'strong_password';
   GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO real_mfa_user;
   ```

4. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

5. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Deploy with Scripts**
   ```bash
   # Copy service files
   sudo cp config/real_mfa_gunicorn.service /etc/systemd/system/
   sudo cp config/real_mfa_celery.service /etc/systemd/system/
   sudo cp config/real_mfa_celery_beat.service /etc/systemd/system/
   sudo cp config/nginx_real_mfa.conf /etc/nginx/sites-available/
   
   # Enable and start services
   sudo systemctl enable real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat
   sudo systemctl start real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat
   ```

### Environment Setup for Production

#### Required Environment Variables:

```bash
# Django
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-with-get_random_secret_key()>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=real_mfa_db
DB_USER=real_mfa_user
DB_PASSWORD=<strong-password>
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-specific-password>

# Frontend
FRONTEND_URL=https://your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

### Security Checklist

- [ ] Generate unique SECRET_KEY for production
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Set up HTTPS/SSL with Let's Encrypt
- [ ] Configure PostgreSQL with strong password
- [ ] Enable firewall (UFW)
- [ ] Use environment variables for all secrets
- [ ] Configure CORS properly
- [ ] Enable CSRF protection
- [ ] Set up regular backups

### Monitoring

Monitor your application:
```bash
bash config/monitor.sh
```

Check logs:
```bash
sudo tail -f /var/log/real_mfa_gunicorn_error.log
sudo tail -f /var/log/real_mfa_celery_worker.log
```

### Deployment

For each update:
```bash
# Pull latest code
git pull origin main

# Activate venv
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart real_mfa_gunicorn
```

Or use the automated script:
```bash
bash config/deploy.sh
```

### Troubleshooting

**Services not starting?**
```bash
sudo systemctl status real_mfa_gunicorn
journalctl -u real_mfa_gunicorn -n 50
```

**Database connection error?**
```bash
psql -U real_mfa_user -d real_mfa_db -h localhost
```

**Celery tasks not running?**
```bash
celery -A Real_MFA inspect active
redis-cli ping
```

### Documentation

- [Complete Deployment Guide](docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md)
- [Quick Reference Commands](config/QUICK_REFERENCE.md)
- [Pre-Deployment Checklist](config/PRE_DEPLOYMENT_CHECKLIST.md)

### Support

For more information, refer to the documentation files in the `docs/` and `config/` directories.
