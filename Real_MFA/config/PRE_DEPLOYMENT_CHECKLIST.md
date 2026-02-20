# Real_MFA Pre-Deployment Checklist
# Complete ALL items before deploying to production!

## 📋 CODE REVIEW
- [ ] All tests pass: `python manage.py test`
- [ ] No debug print statements left in code
- [ ] No hardcoded credentials in code
- [ ] All imports are correct and used
- [ ] Code follows PEP 8 (run `black` or `flake8`)
- [ ] Static type checking passes (optional: `mypy`)
- [ ] Code reviewed by team member

## 🔐 SECURITY
- [ ] `DEBUG = False` in production settings
- [ ] `SECRET_KEY` is strong and unique (use `get_random_secret_key()`)
- [ ] `.env` file is in `.gitignore` ✅
- [ ] `.env.example` exists with placeholder values
- [ ] No secrets in git history: `git log --grep="password\|key\|token"`
- [ ] HTTPS/SSL enforced: `SECURE_SSL_REDIRECT = True`
- [ ] CSRF protection enabled: `CSRF_MIDDLEWARE` present
- [ ] CORS properly configured (not `*`)
- [ ] `ALLOWED_HOSTS` properly set
- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `SECURE_CONTENT_SECURITY_POLICY` configured
- [ ] Database password is strong
- [ ] Redis password set (if accessible externally)

## 🗄️ DATABASE
- [ ] PostgreSQL installed and running
- [ ] Database created: `real_mfa_db`
- [ ] Database user created: `real_mfa_user`
- [ ] Database user has limited privileges
- [ ] All migrations applied: `python manage.py migrate`
- [ ] Database backup procedure tested
- [ ] Connection string correct in `.env`
- [ ] Database user can only connect from localhost

## 📦 DEPENDENCIES
- [ ] All Python dependencies in `requirements.txt`
- [ ] Python version specified (3.11+)
- [ ] Virtual environment created and activated
- [ ] No obsolete or unused packages
- [ ] Django version compatible with all apps
- [ ] Celery version compatible with Redis
- [ ] All dependencies tested and working

## 🌐 STATIC & MEDIA FILES
- [ ] `STATIC_URL` properly configured
- [ ] `STATIC_ROOT` points to correct directory
- [ ] `collectstatic` runs without errors
- [ ] CSS/JS minified (optional but recommended)
- [ ] Media directory permissions set correctly
- [ ] `.env` includes correct media settings

## 🔄 CELERY & BACKGROUND TASKS
- [ ] Redis installed and running
- [ ] Celery configuration in settings
- [ ] Celery beat database migrations done
- [ ] High-priority tasks identified
- [ ] Task timeouts configured appropriately
- [ ] Celery worker restart policy configured
- [ ] Celery beat enabled for scheduled tasks

## 🔌 SERVICES
- [ ] Gunicorn installed and configured
- [ ] Gunicorn worker count appropriate (3-4 for small droplets)
- [ ] Gunicorn timeout set (60-300 seconds)
- [ ] Systemd service files created for all services
- [ ] All services enabled: `systemctl enable ...`
- [ ] Service restart policies set to `always`

## 🌍 NGINX
- [ ] Nginx installed
- [ ] Nginx config validates: `nginx -t`
- [ ] Upstream socket path matches Gunicorn config
- [ ] Static files location correct
- [ ] Media files location correct
- [ ] Logs directory exists and writable
- [ ] SSL certificate paths correct

## 🔒 SSL/HTTPS
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] Certbot installed and configured
- [ ] Auto-renewal scheduled
- [ ] Certificate renewal dry-run passes: `certbot renew --dry-run`
- [ ] HTTPS enforces SSL redirect
- [ ] HSTS headers enabled
- [ ] Certificate valid for all domain variants

## 📧 EMAIL
- [ ] Email backend configured correctly
- [ ] SMTP credentials valid
- [ ] Test email sends successfully
- [ ] Email templates created
- [ ] Sender email address set
- [ ] Email rate limiting configured (optional)

## 📊 MONITORING & LOGGING
- [ ] Logging configured for production
- [ ] Log files have rotation policy
- [ ] Log level appropriate (INFO or WARNING, not DEBUG)
- [ ] Sentry configured (optional but recommended)
- [ ] Monitoring script created and tested
- [ ] Health check endpoint available
- [ ] Error alerts configured

## 🏗️ INFRASTRUCTURE
- [ ] Droplet IP: 143.110.139.119 ✅
- [ ] SSH key-based authentication only
- [ ] Password auth disabled in SSH config
- [ ] UFW firewall configured correctly
- [ ] Only required ports open (22, 80, 443)
- [ ] SSH port changed from 22 (optional but recommended)
- [ ] Non-root user created for app (`realuser`)
- [ ] File permissions correct (no world-writable files)

## 🔍 ADMIN & MAINTENANCE
- [ ] Superuser created
- [ ] Admin panel accessible and functional
- [ ] Admin password secure
- [ ] Django admin login attempted successfully
- [ ] Backup strategy documented
- [ ] Backup tested (restore from backup)
- [ ] Logs directory structure created
- [ ] Cron job for backups scheduled

## 🧪 TESTING (PRODUCTION)
- [ ] Visit https://your-domain.com in browser
- [ ] Admin panel works: https://your-domain.com/admin/
- [ ] API endpoints respond correctly
- [ ] Database queries work (check logs)
- [ ] Celery tasks execute successfully
- [ ] Emails send correctly
- [ ] Static files load (CSS/JS/images)
- [ ] Media files accessible (if applicable)
- [ ] HTTPS redirect works
- [ ] All authentication flows tested
- [ ] All MFA flows tested

## 📱 FRONTEND (if applicable)
- [ ] Frontend API URL points to production
- [ ] Frontend environment variables correct
- [ ] CORS allows frontend origin
- [ ] Login flow works end-to-end
- [ ] JWT tokens valid and refreshable
- [ ] MFA flows work in frontend
- [ ] Error messages user-friendly

## 📲 NOTIFICATIONS
- [ ] Email notifications tested
- [ ] Notification queue working (Celery)
- [ ] Notification templates rendering correctly
- [ ] OTP emails sending
- [ ] Verification emails sending
- [ ] Alert emails to admins configured

## 🔄 DEPLOYMENT PROCESS
- [ ] Deployment script created and tested
- [ ] Rollback procedure documented
- [ ] Blue-green deployment possible (optional)
- [ ] Zero-downtime deployment tested (if applicable)
- [ ] Deployment window scheduled
- [ ] Team notified of deployment time
- [ ] Post-deployment verification steps documented

## 👥 TEAM & STAKEHOLDERS
- [ ] Team trained on maintenance tasks
- [ ] Documentation complete and shared
- [ ] Emergency contacts listed
- [ ] Support process documented
- [ ] Incident response plan in place
- [ ] Stakeholders notified of go-live

## 📋 POST-DEPLOYMENT (After going live)
- [ ] All services running: `systemctl status ...`
- [ ] No error logs: `tail -f /var/log/.../error.log`
- [ ] Response times acceptable
- [ ] Database not growing unexpectedly
- [ ] Disk space sufficient
- [ ] Memory usage acceptable
- [ ] CPU usage normal
- [ ] Network traffic stable

## 🎯 FINAL SIGN-OFF
- [ ] Project Lead approval
- [ ] Security review passed
- [ ] Performance acceptable
- [ ] All stakeholders satisfied

---

## DEPLOYMENT COMMAND (After checklist complete)
```bash
# SSH to droplet
ssh realuser@143.110.139.119

# Run deployment script
bash ~/real_mfa/config/deploy.sh

# Verify everything works
bash ~/real_mfa/config/monitor.sh
```

## ROLLBACK COMMAND (If issues occur)
```bash
cd ~/real_mfa
git revert HEAD
git push origin main
bash config/deploy.sh
```

---

**Checklist completed by:** ___________________
**Date:** ___________________
**Notes:** ___________________________________________________________________

