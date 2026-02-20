#!/bin/bash
# Real_MFA Production Deployment Script for DigitalOcean
# Run: bash deploy.sh
# This script automates the entire deployment process

set -e  # Exit on error

echo "================================"
echo "Real_MFA Production Deployment"
echo "================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/realuser/real_mfa"
VENV_DIR="${PROJECT_DIR}/venv"
WORKING_DIR="${PROJECT_DIR}/Real_MFA"

# Step 1: Pull latest code
echo -e "\n${YELLOW}Step 1: Pulling latest code from repository...${NC}"
cd ${PROJECT_DIR}
git pull origin main
echo -e "${GREEN}✓ Code pulled successfully${NC}"

# Step 2: Activate venv and install dependencies
echo -e "\n${YELLOW}Step 2: Installing Python dependencies...${NC}"
source ${VENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Run migrations
echo -e "\n${YELLOW}Step 3: Running database migrations...${NC}"
cd ${WORKING_DIR}
python manage.py migrate
echo -e "${GREEN}✓ Migrations completed${NC}"

# Step 4: Collect static files
echo -e "\n${YELLOW}Step 4: Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Static files collected${NC}"

# Step 5: Restart services
echo -e "\n${YELLOW}Step 5: Restarting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl restart real_mfa_gunicorn
sudo systemctl restart real_mfa_celery
sudo systemctl restart real_mfa_celery_beat
sudo systemctl reload nginx
echo -e "${GREEN}✓ Services restarted${NC}"

# Step 6: Health check
echo -e "\n${YELLOW}Step 6: Running health checks...${NC}"
sleep 2

# Check Gunicorn
if sudo systemctl is-active --quiet real_mfa_gunicorn; then
    echo -e "${GREEN}✓ Gunicorn is running${NC}"
else
    echo -e "${RED}✗ Gunicorn failed to start${NC}"
    exit 1
fi

# Check Celery
if sudo systemctl is-active --quiet real_mfa_celery; then
    echo -e "${GREEN}✓ Celery worker is running${NC}"
else
    echo -e "${RED}✗ Celery worker failed to start${NC}"
    exit 1
fi

# Check Celery Beat
if sudo systemctl is-active --quiet real_mfa_celery_beat; then
    echo -e "${GREEN}✓ Celery beat is running${NC}"
else
    echo -e "${RED}✗ Celery beat failed to start${NC}"
    exit 1
fi

# Check PostgreSQL
if sudo systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not running${NC}"
    exit 1
fi

# Check Nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx failed to start${NC}"
    exit 1
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✓ Deployment successful!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "\nYour application is live at:"
echo -e "${YELLOW}https://your-domain.com${NC}"
echo -e "\nCheck logs:"
echo -e "  Gunicorn: tail -f /var/log/real_mfa_gunicorn_error.log"
echo -e "  Celery: tail -f /var/log/real_mfa_celery_worker.log"
echo -e "  Nginx: tail -f /var/log/nginx/real_mfa_error.log"
