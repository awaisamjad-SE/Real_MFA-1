#!/bin/bash
# Real_MFA Installation Script for Ubuntu/DigitalOcean
# Run: sudo bash setup.sh

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Real_MFA Ubuntu Installation Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo -e "${YELLOW}⚠️  This script should not be run as root for installation.${NC}"
   echo -e "${YELLOW}However, sudo will be used for system commands.${NC}"
fi

# 1. Update system
echo -e "\n${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
echo -e "${GREEN}✓ System updated${NC}"

# 2. Install Python and dependencies
echo -e "\n${YELLOW}Step 2: Installing Python and dependencies...${NC}"
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git curl wget
python3.11 --version
echo -e "${GREEN}✓ Python installed${NC}"

# 3. Install PostgreSQL
echo -e "\n${YELLOW}Step 3: Installing PostgreSQL...${NC}"
sudo apt install -y postgresql postgresql-contrib postgresql-client
sudo systemctl start postgresql
sudo systemctl enable postgresql
echo -e "${GREEN}✓ PostgreSQL installed and started${NC}"

# 4. Install Redis
echo -e "\n${YELLOW}Step 4: Installing Redis...${NC}"
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping
echo -e "${GREEN}✓ Redis installed and started${NC}"

# 5. Install Nginx
echo -e "\n${YELLOW}Step 5: Installing Nginx...${NC}"
sudo apt install -y nginx
sudo systemctl enable nginx
echo -e "${GREEN}✓ Nginx installed${NC}"

# 6. Setup UFW Firewall
echo -e "\n${YELLOW}Step 6: Configuring firewall...${NC}"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable -y
sudo ufw status
echo -e "${GREEN}✓ Firewall configured${NC}"

# 7. Create application user
echo -e "\n${YELLOW}Step 7: Creating application user...${NC}"
if ! id "realuser" &>/dev/null; then
    sudo useradd -m -s /bin/bash realuser
    sudo usermod -aG sudo realuser
    echo -e "${GREEN}✓ User 'realuser' created${NC}"
else
    echo -e "${YELLOW}⚠️  User 'realuser' already exists${NC}"
fi

# 8. Setup application directory
echo -e "\n${YELLOW}Step 8: Setting up application directory...${NC}"
sudo mkdir -p /var/www/real_mfa
sudo chown -R realuser:realuser /var/www/real_mfa
echo -e "${GREEN}✓ Application directory ready${NC}"

# 9. Create PostgreSQL database and user
echo -e "\n${YELLOW}Step 9: Creating PostgreSQL database...${NC}"
sudo -u postgres psql <<EOF
DO
\$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'real_mfa_user') THEN
        CREATE ROLE real_mfa_user LOGIN PASSWORD 'change_this_password';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE real_mfa_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'real_mfa_db')\gexec

ALTER ROLE real_mfa_user SET client_encoding TO 'utf8';
ALTER ROLE real_mfa_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE real_mfa_user SET default_transaction_deferrable TO on;
ALTER ROLE real_mfa_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO real_mfa_user;
EOF
echo -e "${GREEN}✓ PostgreSQL database created${NC}"

# 10. Test database connection
echo -e "\n${YELLOW}Step 10: Testing database connection...${NC}"
if psql -U real_mfa_user -d real_mfa_db -h localhost -c "SELECT 1;" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed - check credentials${NC}"
    echo -e "${YELLOW}Update .env file with correct database password${NC}"
fi

# 11. Install Supervisor (for process management)
echo -e "\n${YELLOW}Step 11: Installing Supervisor...${NC}"
sudo apt install -y supervisor
echo -e "${GREEN}✓ Supervisor installed${NC}"

# 12. Install Certbot for SSL
echo -e "\n${YELLOW}Step 12: Installing Certbot for SSL...${NC}"
sudo apt install -y certbot python3-certbot-nginx
echo -e "${GREEN}✓ Certbot installed${NC}"

# 13. Create logs directory
echo -e "\n${YELLOW}Step 13: Creating log directories...${NC}"
sudo mkdir -p /var/log/real_mfa
sudo chown -R realuser:realuser /var/log/real_mfa
echo -e "${GREEN}✓ Log directories created${NC}"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Switch to realuser:"
echo -e "   ${BLUE}su - realuser${NC}"
echo ""
echo "2. Clone the repository:"
echo -e "   ${BLUE}git clone <repo-url> ~/real_mfa${NC}"
echo -e "   ${BLUE}cd ~/real_mfa/Real_MFA${NC}"
echo ""
echo "3. Create virtual environment:"
echo -e "   ${BLUE}python3.11 -m venv ../venv${NC}"
echo -e "   ${BLUE}source ../venv/bin/activate${NC}"
echo ""
echo "4. Install Python dependencies:"
echo -e "   ${BLUE}pip install -r requirements.txt${NC}"
echo ""
echo "5. Setup environment file:"
echo -e "   ${BLUE}cp .env.example .env${NC}"
echo -e "   ${BLUE}nano .env${NC}"
echo ""
echo "⚠️  Important: Update .env with your actual values:"
echo "   - SECRET_KEY: Generate with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
echo "   - DB_PASSWORD: Change from 'change_this_password'"
echo "   - EMAIL credentials"
echo "   - FRONTEND_URL"
echo ""
echo "6. Run migrations:"
echo -e "   ${BLUE}python manage.py migrate${NC}"
echo ""
echo "7. Collect static files:"
echo -e "   ${BLUE}python manage.py collectstatic --noinput${NC}"
echo ""
echo "8. Create superuser:"
echo -e "   ${BLUE}python manage.py createsuperuser${NC}"
echo ""
echo "9. Copy configuration files:"
echo -e "   ${BLUE}sudo cp config/*.service /etc/systemd/system/${NC}"
echo -e "   ${BLUE}sudo cp config/nginx_real_mfa.conf /etc/nginx/sites-available/real_mfa${NC}"
echo ""
echo "10. Read deployment guide:"
echo -e "   ${BLUE}docs/DIGITALOCEAN_DROPLET_COMPLETE_SETUP.md${NC}"
echo ""
echo -e "${GREEN}System is ready for Django application deployment!${NC}"
