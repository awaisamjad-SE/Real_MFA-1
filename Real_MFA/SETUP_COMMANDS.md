# Real_MFA - Quick Setup Command Reference
# Copy-paste each section when needed

# =============================================================================
# SECTION 1: GENERATE DJANGO SECRET KEY (Run on local machine)
# =============================================================================

python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Output: Copy the result and paste in .env as SECRET_KEY


# =============================================================================
# SECTION 2: SSH INTO DROPLET (From your local machine)
# =============================================================================

ssh realuser@143.110.139.119
# If first time, might ask to accept key - type "yes"


# =============================================================================
# SECTION 3: INITIAL SETUP (Run as root on droplet)
# =============================================================================

sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# Create non-root user
adduser realuser
usermod -aG sudo realuser
su - realuser

# Generate SSH key (run on LOCAL machine, not droplet!)
# Then add to droplet: cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git
sudo apt install -y postgresql postgresql-contrib postgresql-client
sudo apt install -y nginx redis-server supervisor


# =============================================================================
# SECTION 4: POSTGRESQL SETUP (Run on droplet)
# =============================================================================

sudo -u postgres psql

# Inside psql terminal, paste this:
CREATE DATABASE real_mfa_db;
CREATE USER real_mfa_user WITH PASSWORD 'your_strong_password_here_123!@#';
ALTER ROLE real_mfa_user SET client_encoding TO 'utf8';
ALTER ROLE real_mfa_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE real_mfa_user SET default_transaction_deferrable TO on;
ALTER ROLE real_mfa_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO real_mfa_user;
\q

# Test connection
psql -U real_mfa_user -d real_mfa_db -h localhost -c "SELECT version();"


# =============================================================================
# SECTION 5: CLONE AND SETUP REAL_MFA (Run on droplet as realuser)
# =============================================================================

cd /home/realuser
git clone https://github.com/your-username/Real_MFA.git real_mfa
cd real_mfa/Real_MFA

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
# Copy content from example.env and fill in YOUR values
# Save: Ctrl+X, Y, Enter


# =============================================================================
# SECTION 6: DJANGO MIGRATIONS (Run on droplet)
# =============================================================================

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Follow prompts


# =============================================================================
# SECTION 7: COPY CONFIGURATION FILES (From your local machine)
# =============================================================================

# Copy all .service files:
scp config/real_mfa_gunicorn.service realuser@143.110.139.119:/home/realuser/
scp config/real_mfa_celery.service realuser@143.110.139.119:/home/realuser/
scp config/real_mfa_celery_beat.service realuser@143.110.139.119:/home/realuser/

# SSH in and move to systemd:
ssh realuser@143.110.139.119
sudo mv ~/real_mfa_*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Copy nginx config:
scp config/nginx_real_mfa.conf realuser@143.110.139.119:/home/realuser/
ssh realuser@143.110.139.119
sudo mv ~/nginx_real_mfa.conf /etc/nginx/sites-available/real_mfa
sudo ln -s /etc/nginx/sites-available/real_mfa /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx


# =============================================================================
# SECTION 8: START ALL SERVICES (Run on droplet)
# =============================================================================

sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl start real_mfa_gunicorn
sudo systemctl start real_mfa_celery
sudo systemctl start real_mfa_celery_beat
sudo systemctl start nginx

# Enable auto-start
sudo systemctl enable postgresql redis-server real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx


# =============================================================================
# SECTION 9: GET SSL CERTIFICATE (Run on droplet)
# =============================================================================

sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
# Follow prompts

# Test renewal
sudo certbot renew --dry-run


# =============================================================================
# SECTION 10: VERIFY EVERYTHING (Run on droplet)
# =============================================================================

bash ~/real_mfa/config/monitor.sh
# All checks should show ✓


# =============================================================================
# SECTION A: DAILY OPERATIONS (Use for regular work)
# =============================================================================

# SSH in
ssh realuser@143.110.139.119

# Deploy updates (pull code + migrate + restart)
bash ~/real_mfa/config/deploy.sh

# Check health
bash ~/real_mfa/config/monitor.sh

# View error logs
sudo tail -f /var/log/real_mfa_gunicorn_error.log

# Backup database
bash ~/real_mfa/config/backup.sh

# Restart all services
sudo systemctl restart real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx


# =============================================================================
# SECTION B: TROUBLESHOOTING (When something breaks)
# =============================================================================

# Check all services
sudo systemctl status real_mfa_gunicorn real_mfa_celery real_mfa_celery_beat nginx postgresql redis-server

# View recent errors
sudo journalctl -u real_mfa_gunicorn -n 50
sudo journalctl -u real_mfa_celery -n 50

# Test database connection
psql -U real_mfa_user -d real_mfa_db -h localhost -c "SELECT 1;"

# Test Redis connection
redis-cli ping

# Restart Gunicorn
sudo systemctl restart real_mfa_gunicorn
sudo systemctl status real_mfa_gunicorn

# View Gunicorn socket
ls -la /run/gunicorn_real_mfa.sock

# Check disk space
df -h

# Check memory
free -h

# Rebuild static files
python manage.py collectstatic --noinput --clear
sudo systemctl restart real_mfa_gunicorn


# =============================================================================
# SECTION C: EMERGENCY ROLLBACK (If deployment fails)
# =============================================================================

cd ~/real_mfa
git status  # See what changed
git log --oneline -5  # See recent commits
git revert HEAD  # Revert last commit
git push origin main  # Push changes
bash config/deploy.sh  # Redeploy


# =============================================================================
# SECTION D: CRON JOBS (For automation)
# =============================================================================

# Edit crontab
crontab -e

# Add these lines:

# Daily backup at 2 AM
0 2 * * * /home/realuser/real_mfa/config/backup.sh

# Health check every 5 minutes
*/5 * * * * /home/realuser/real_mfa/config/monitor.sh


# =============================================================================
# SECTION E: MANAGEMENT COMMANDS
# =============================================================================

# SSH in first
ssh realuser@143.110.139.119
cd ~/real_mfa/Real_MFA
source ../venv/bin/activate

# Create admin user
python manage.py createsuperuser

# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Check migrations status
python manage.py showmigrations

# Run specific migration
python manage.py migrate accounts 0005

# View all management commands
python manage.py help


# =============================================================================
# SECTION F: CELERY OPERATIONS
# =============================================================================

# Check active tasks
celery -A Real_MFA inspect active

# Check stats
celery -A Real_MFA inspect stats

# List all registered tasks
celery -A Real_MFA inspect registered

# Purge all pending tasks
celery -A Real_MFA purge

# View worker logs
sudo tail -f /var/log/real_mfa_celery_worker.log


# =============================================================================
# DONE! YOUR SETUP IS COMPLETE
# =============================================================================

# Your site is now live at:
# https://your-domain.com

# Admin panel at:
# https://your-domain.com/admin/

# For daily commands, reference QUICK_REFERENCE.md

