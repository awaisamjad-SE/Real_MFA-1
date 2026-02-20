# Real_MFA Production Deployment Quick Reference
# Copy-paste ready commands for your DigitalOcean droplet

## 🔐 SSH INTO DROPLET
ssh realuser@143.110.139.119

## 📁 NAVIGATE TO PROJECT
cd /home/realuser/real_mfa/Real_MFA
source ../venv/bin/activate

## 🚀 QUICK DEPLOYMENT (runs all steps)
bash config/deploy.sh

## 🔄 RESTART ALL SERVICES
sudo systemctl restart real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx

## 📊 CHECK ALL SERVICES STATUS
sudo systemctl status real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx postgresql redis-server

## 📝 VIEW LOGS

### Gunicorn (Django app)
sudo tail -f /var/log/real_mfa_gunicorn_error.log
sudo tail -f /var/log/real_mfa_gunicorn_access.log

### Celery (Background tasks)
sudo tail -f /var/log/real_mfa_celery_worker.log
sudo tail -f /var/log/real_mfa_celery_beat.log

### Nginx (Web server)
sudo tail -f /var/log/nginx/real_mfa_error.log
sudo tail -f /var/log/nginx/real_mfa_access.log

### Full system logs
sudo journalctl -u real_mfa_gunicorn -n 100
sudo journalctl -u real_mfa_celery -n 100
sudo journalctl -u real_mfa_celery_beat -n 100

## 🗄️ DATABASE OPERATIONS

### Connect to database
psql -U real_mfa_user -d real_mfa_db -h localhost

### Backup database
sudo -u postgres pg_dump real_mfa_db > backup_$(date +%Y%m%d).sql

### Restore database
sudo -u postgres psql real_mfa_db < backup_20250805.sql

### List all tables
psql -U real_mfa_user -d real_mfa_db -c "\dt"

## 🔄 UPDATE CODE & RUN MIGRATIONS

### Pull latest code
cd /home/realuser/real_mfa
git pull origin main

### Migrate database
cd Real_MFA
python manage.py migrate

### Collect static files
python manage.py collectstatic --noinput --clear

### Restart Gunicorn
sudo systemctl restart real_mfa_gunicorn

## 🧪 CELERY TASKS

### Check active tasks
celery -A Real_MFA inspect active

### Check registered tasks
celery -A Real_MFA inspect registered

### Purge all pending tasks
celery -A Real_MFA purge

### Check Celery workers
celery -A Real_MFA inspect stats

## 🔍 SYSTEM MONITORING

### Disk usage
df -h

### Memory usage
free -h

### Running processes
ps aux | grep real_mfa

### Port usage
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000

## 🔒 SECURITY

### UFW firewall status
sudo ufw status

### Open port
sudo ufw allow 22/tcp

### Check SSL certificate
sudo certbot certificates

### Renew SSL certificate
sudo certbot renew

### Dry-run SSL renewal
sudo certbot renew --dry-run

## 📊 PERFORMANCE TUNING

### Check PostgreSQL slow queries
sudo tail -f /var/log/postgresql/postgresql-*.log | grep duration

### Monitor system resources
watch -n 1 'free -h; echo "---"; df -h'

### Check nginx connection count
netstat -an | grep ESTABLISHED | wc -l

## 🆘 TROUBLESHOOTING

### If Gunicorn fails to start
sudo systemctl restart real_mfa_gunicorn
sudo journalctl -u real_mfa_gunicorn -n 50 --no-pager

### If database connection fails
psql -U real_mfa_user -d real_mfa_db -c "SELECT 1"

### If Celery not processing tasks
redis-cli ping  # Should respond PONG
celery -A Real_MFA inspect active

### If nginx shows 502 Bad Gateway
sudo systemctl restart real_mfa_gunicorn
ls -la /run/gunicorn_real_mfa.sock

### If static files not loading
python manage.py collectstatic --noinput --clear
sudo systemctl restart real_mfa_gunicorn

### Clear Django cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

## 📋 COMMON TASKS

### Create superuser
python manage.py createsuperuser

### Run management command
python manage.py <command>

### Install new package
source ../venv/bin/activate
pip install package_name
pip freeze > requirements.txt
# Commit changes and redeploy

### Check disk space before backup
du -sh /home/realuser/real_mfa

### Compress old logs
gzip /var/log/nginx/real_mfa_access.log.*

## 🔐 SECURITY BEST PRACTICES

✓ SSH key-only authentication
✓ Firewall (ufw) enabled
✓ HTTPS/SSL everywhere
✓ .env file in .gitignore
✓ Never commit secrets to repo
✓ Regular backups (daily)
✓ Update system: sudo apt update && sudo apt upgrade -y
✓ Monitor logs regularly: tail -f /var/log/...
✓ PostgreSQL user with limited privileges
✓ Strong database password
✓ Rate limiting enabled on API
✓ CSRF protection enabled
✓ CORS properly configured

## 📞 EMERGENCY REVERT CHANGES

If deployment breaks production:

1. Revert to last working commit:
   git revert HEAD
   git push origin main

2. Check status:
   sudo systemctl status real_mfa_gunicorn

3. Check logs:
   sudo journalctl -u real_mfa_gunicorn -n 200 --no-pager

4. Manually run deployment if needed:
   bash config/deploy.sh

## 📱 MONITORING SETUP (Optional)

Install monitoring tools:
```bash
sudo apt install htop  # System monitoring
sudo apt install nload # Network monitoring
```

Real-time monitoring:
```bash
watch -n 1 'htop -p $(pidof gunicorn)'
```

---
Last Updated: 2025-01-08
For full guide, see: DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md
