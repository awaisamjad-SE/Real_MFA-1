# Real_MFA - Ubuntu Installation Guide

For complete deployment info, see: [DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md](docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md)

## Quick Installation (5 minutes)

### 1. Automated System Setup

Run this command to install all system dependencies:

```bash
sudo bash setup.sh
```

This will automatically:
- Update system packages
- Install Python 3.11, PostgreSQL, Redis, Nginx
- Create database and user
- Configure firewall
- Create application user

### 2. Manual Setup (If Preferred)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Install Nginx
sudo apt install -y nginx

# Install Supervisor
sudo apt install -y supervisor
```

## Application Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/Real_MFA.git ~/real_mfa
cd ~/real_mfa/Real_MFA
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv ../venv
source ../venv/bin/activate
```

### 3. Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env

# IMPORTANT: Fill in these values:
# - ENVIRONMENT=production
# - SECRET_KEY=<generate-with-get_random_secret_key()>
# - DB_PASSWORD=<strong-password>
# - EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
# - ALLOWED_HOSTS=your-domain.com
# - FRONTEND_URL=https://your-domain.com
```

### 5. Database Setup

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE real_mfa_db;
CREATE USER real_mfa_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO real_mfa_user;
\q

# Test connection
psql -U real_mfa_user -d real_mfa_db -h localhost -c "SELECT 1;"
```

### 6. Django Setup

```bash
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Test locally (optional)
python manage.py runserver 0.0.0.0:8000
# Visit: http://localhost:8000/admin/
```

### 7. Copy Service Files

```bash
# Copy systemd service files
sudo cp config/real_mfa_gunicorn.service /etc/systemd/system/
sudo cp config/real_mfa_celery.service /etc/systemd/system/
sudo cp config/real_mfa_celery_beat.service /etc/systemd/system/

# Copy Nginx config
sudo cp config/nginx_real_mfa.conf /etc/nginx/sites-available/real_mfa
sudo ln -s /etc/nginx/sites-available/real_mfa /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 8. Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx postgresql redis-server

# Start services
sudo systemctl start real_mfa_gunicorn
sudo systemctl start real_mfa_celery
sudo systemctl start real_mfa_celery_beat
```

### 9. Get SSL Certificate

```bash
# Update your domain in Nginx config first
sudo nano /etc/nginx/sites-available/real_mfa
# Replace "your-domain.com" with your actual domain

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
# Follow the prompts
```

### 10. Verify Everything Works

```bash
# Check all services
sudo systemctl status real_mfa_gunicorn
sudo systemctl status real_mfa_celery
sudo systemctl status real_mfa_celery_beat
sudo systemctl status nginx

# Or use the monitor script
bash config/monitor.sh
```

## Testing Your Setup

### 1. Check Admin Panel

Visit: `https://your-domain.com/admin/`
- Login with superuser credentials

### 2. Check Health

```bash
bash config/monitor.sh
# All checks should show ✓
```

### 3. View Logs

```bash
# Gunicorn
sudo tail -f /var/log/real_mfa_gunicorn_error.log

# Celery
sudo tail -f /var/log/real_mfa_celery_worker.log

# Nginx
sudo tail -f /var/log/nginx/real_mfa_error.log
```

## Common Issues

### Port Already in Use

```bash
# Check which process is using port
sudo lsof -i :8000
sudo lsof -i :80
sudo lsof -i :443

# Kill if needed
kill -9 <PID>
```

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U real_mfa_user -d real_mfa_db -h localhost

# Check .env has correct credentials
cat .env | grep DB_
```

### Static Files Not Loading

```bash
# Collect again
python manage.py collectstatic --noinput --clear

# Check permissions
ls -la /var/www/real_mfa/staticfiles/

# Restart Gunicorn
sudo systemctl restart real_mfa_gunicorn
```

### Celery Not Running

```bash
# Check Redis
redis-cli ping  # Should respond PONG

# Check Celery
celery -A Real_MFA inspect active

# View logs
sudo tail -f /var/log/real_mfa_celery_worker.log
```

## Backup and Maintenance

### Backup Database

```bash
sudo -u postgres pg_dump real_mfa_db > ~/real_mfa_backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
sudo -u postgres psql real_mfa_db < ~/real_mfa_backup_20260220.sql
```

### Update Code

```bash
cd ~/real_mfa
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart real_mfa_gunicorn
```

### Setup Auto-Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /home/realuser/real_mfa/config/backup.sh
```

## Production Checklist

- [ ] Environment variables configured (.env file)
- [ ] Database credentials updated
- [ ] SECRET_KEY is unique and strong
- [ ] Email settings configured
- [ ] Domain name pointing to server IP
- [ ] SSL certificate installed
- [ ] All services running and enabled
- [ ] Firewall properly configured
- [ ] Backups scheduled
- [ ] Monitoring enabled (monitor.sh)
- [ ] Admin panel accessible
- [ ] Health check passes

## Next Steps

1. **Read Full Documentation:** [docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md](docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md)
2. **Quick Commands:** [config/QUICK_REFERENCE.md](config/QUICK_REFERENCE.md)
3. **Troubleshooting:** [config/QUICK_REFERENCE.md#troubleshooting](config/QUICK_REFERENCE.md#troubleshooting)
4. **API Endpoints:** See README.md
5. **Architecture:** [docs/README_REFACTORED_ARCHITECTURE.md](docs/README_REFACTORED_ARCHITECTURE.md)

## Getting Help

If you encounter issues:

1. Check the logs: `sudo tail -f /var/log/real_mfa_*.log`
2. Run health check: `bash config/monitor.sh`
3. See [QUICK_REFERENCE.md](config/QUICK_REFERENCE.md) troubleshooting section
4. Review [DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md](docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md)

---

**Installation Time:** ~15-20 minutes
**Status:** ✅ Production Ready
**Last Updated:** February 20, 2026
