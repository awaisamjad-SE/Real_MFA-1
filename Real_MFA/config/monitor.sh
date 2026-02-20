#!/bin/bash
# Real_MFA Monitoring & Health Check Script
# Run: bash monitor.sh
# Or add to crontab: */5 * * * * /home/realuser/real_mfa/config/monitor.sh

set -e

# Configuration
LOG_FILE="/var/log/real_mfa_monitor.log"
EMAIL="your-email@example.com"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check service
check_service() {
    local service=$1
    if sudo systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is DOWN"
        echo "[$TIMESTAMP] ALERT: $service is down" >> $LOG_FILE
        return 1
    fi
}

# Function to check port
check_port() {
    local port=$1
    local name=$2
    if netstat -tuln | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} $name (port $port) is listening"
        return 0
    else
        echo -e "${RED}✗${NC} $name (port $port) is NOT listening"
        echo "[$TIMESTAMP] ALERT: $name is not listening on port $port" >> $LOG_FILE
        return 1
    fi
}

# Function to check disk space
check_disk() {
    local usage=$(df /home/realuser | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 80 ]; then
        echo -e "${RED}✗${NC} Disk usage is ${usage}% (HIGH)"
        echo "[$TIMESTAMP] ALERT: Disk usage at ${usage}%" >> $LOG_FILE
        return 1
    else
        echo -e "${GREEN}✓${NC} Disk usage is ${usage}%"
        return 0
    fi
}

# Function to check memory
check_memory() {
    local usage=$(free | awk 'NR==2 {printf("%.0f", $3/$2 * 100)}')
    if [ "$usage" -gt 85 ]; then
        echo -e "${RED}✗${NC} Memory usage is ${usage}% (HIGH)"
        echo "[$TIMESTAMP] ALERT: Memory usage at ${usage}%" >> $LOG_FILE
        return 1
    else
        echo -e "${GREEN}✓${NC} Memory usage is ${usage}%"
        return 0
    fi
}

# Function to check database
check_database() {
    if psql -U real_mfa_user -d real_mfa_db -h localhost -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL database connection OK"
        return 0
    else
        echo -e "${RED}✗${NC} PostgreSQL database connection FAILED"
        echo "[$TIMESTAMP] ALERT: Database connection failed" >> $LOG_FILE
        return 1
    fi
}

# Function to check Redis
check_redis() {
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis server OK"
        return 0
    else
        echo -e "${RED}✗${NC} Redis server DOWN"
        echo "[$TIMESTAMP] ALERT: Redis is down" >> $LOG_FILE
        return 1
    fi
}

# Function to check Gunicorn socket
check_gunicorn_socket() {
    if [ -S /run/gunicorn_real_mfa.sock ]; then
        echo -e "${GREEN}✓${NC} Gunicorn socket exists"
        return 0
    else
        echo -e "${RED}✗${NC} Gunicorn socket missing"
        echo "[$TIMESTAMP] ALERT: Gunicorn socket missing" >> $LOG_FILE
        return 1
    fi
}

# Function to check recent errors
check_recent_errors() {
    local errors=$(sudo tail -20 /var/log/real_mfa_gunicorn_error.log 2>/dev/null | grep -c "ERROR\|Traceback\|Exception" || echo 0)
    if [ "$errors" -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} Found $errors errors in recent Gunicorn logs"
        echo "[$TIMESTAMP] WARNING: Found $errors errors in Gunicorn logs" >> $LOG_FILE
        return 1
    else
        echo -e "${GREEN}✓${NC} No recent errors in logs"
        return 0
    fi
}

# Main health check
echo ""
echo "================================"
echo "Real_MFA Health Check - $TIMESTAMP"
echo "================================"
echo ""

FAILED=0

# System checks
echo "📊 SYSTEM HEALTH:"
check_disk || FAILED=$((FAILED + 1))
check_memory || FAILED=$((FAILED + 1))
echo ""

# Service checks
echo "🚀 SERVICES:"
check_service "postgresql" || FAILED=$((FAILED + 1))
check_service "redis-server" || FAILED=$((FAILED + 1))
check_service "real_mfa_gunicorn" || FAILED=$((FAILED + 1))
check_service "real_mfa_celery" || FAILED=$((FAILED + 1))
check_service "real_mfa_celery_beat" || FAILED=$((FAILED + 1))
check_service "nginx" || FAILED=$((FAILED + 1))
echo ""

# Port checks
echo "🔌 PORTS:"
check_port "80" "HTTP" || FAILED=$((FAILED + 1))
check_port "443" "HTTPS" || FAILED=$((FAILED + 1))
check_port "5432" "PostgreSQL" || FAILED=$((FAILED + 1))
check_port "6379" "Redis" || FAILED=$((FAILED + 1))
echo ""

# Connectivity checks
echo "📡 CONNECTIVITY:"
check_database || FAILED=$((FAILED + 1))
check_redis || FAILED=$((FAILED + 1))
check_gunicorn_socket || FAILED=$((FAILED + 1))
echo ""

# Log checks
echo "📝 LOGS:"
check_recent_errors || FAILED=$((FAILED + 1))
echo ""

# Summary
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "[$TIMESTAMP] All health checks passed" >> $LOG_FILE
    exit 0
else
    echo -e "${RED}✗ $FAILED check(s) failed - REVIEW ABOVE${NC}"
    echo "[$TIMESTAMP] $FAILED health check(s) failed" >> $LOG_FILE
    
    # Optional: Send email alert
    # echo "Real_MFA health check failed with $FAILED error(s)" | \
    #     mail -s "⚠️ Real_MFA Alert on $(hostname)" $EMAIL
    
    exit 1
fi
