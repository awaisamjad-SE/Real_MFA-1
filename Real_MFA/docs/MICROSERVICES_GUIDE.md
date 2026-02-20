# ðŸ—ï¸ Microservices Architecture Guide - Real_MFA

## ðŸ“‹ Table of Contents

1. [What are Microservices?](#what-are-microservices)
2. [Microservices vs Monolithic Architecture](#microservices-vs-monolithic-architecture)
3. [Real_MFA as a Microservice](#real_mfa-as-a-microservice)
4. [How to Deploy Real_MFA as Microservice](#how-to-deploy-real_mfa-as-microservice)
5. [Reusability Across Projects](#reusability-across-projects)
6. [Handling Different Account Models](#handling-different-account-models)
7. [Implementation Examples](#implementation-examples)
   - [Example 1: Ecommerce Registration (Node.js)](#example-1-ecommerce-registration)
   - [Example 2: Ecommerce Login with MFA (Node.js)](#example-2-ecommerce-login-with-mfa)
   - [Example 3: Blog with Extended Profile (Python Django)](#example-3-bloguser-with-extended-profile)
   - [Example 4: SaaS Project (Django Solo App)](#example-4-django-saas-project-solo-app)
8. [DigitalOcean Deployment](#digitalocean-deployment)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## What are Microservices?

### ðŸ“Œ **Definition**

Microservices is an **architectural approach** where a large application is broken down into **small, independent, loosely-coupled services** that work together.

---

## DigitalOcean Deployment

If you want to deploy this Real_MFA architecture on DigitalOcean instead of AWS, use the dedicated guide:

- [DIGITALOCEAN_DEPLOYMENT_GUIDE.md](DIGITALOCEAN_DEPLOYMENT_GUIDE.md)

It includes:
- App Platform deployment path
- Droplet + Docker Compose deployment path
- Managed PostgreSQL + Managed Redis setup
- Nginx + SSL (Let's Encrypt)
- Production hardening and troubleshooting checklist

### **Key Characteristics**

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                   MICROSERVICES                         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                         â”‚
â”‚  Service A      Service B      Service C      Service D â”‚
â”‚  (Auth)         (Orders)       (Payments)     (Shipping)â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€       â”€â”€â”€â”€â”€â”€â”€â”€â”€      â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€     â”€â”€â”€â”€â”€â”€â”€â”€â”€â”‚
â”‚  â€¢ Independent  â€¢ Independent  â€¢ Independent  â€¢ Independent
â”‚  â€¢ Own DB       â€¢ Own DB       â€¢ Own DB       â€¢ Own DB  â”‚
â”‚  â€¢ Own Code     â€¢ Own Code     â€¢ Own Code     â€¢ Own Codeâ”‚
â”‚  â€¢ REST/gRPC    â€¢ REST/gRPC    â€¢ REST/gRPC    â€¢ REST/gRPC
â”‚  â€¢ Scalable     â€¢ Scalable     â€¢ Scalable     â€¢ Scalableâ”‚
â”‚                                                         â”‚
â”‚  â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  API Gateway  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º       â”‚
â”‚                 (Routes requests)                       â”‚
â”‚                                                         â”‚
â”‚  â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Event Bus / Message Queue â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
â”‚              (Services communicate)                     â”‚
â”‚                                                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### **Characteristics of Microservices**

| Aspect | Description |
|--------|-------------|
| **Independent Deployment** | Each service deploys separately without affecting others |
| **Loose Coupling** | Services don't depend on internal implementation of others |
| **Single Responsibility** | Each service handles one business capability |
| **Owned Database** | Each service has its own database (Database per Service pattern) |
| **API Communication** | Services communicate via REST/gRPC/message queues |
| **Scalability** | Scale individual services based on demand |
| **Technology Flexibility** | Each service can use different tech stack |
| **Independent Teams** | Teams can develop, test, deploy independently |

### **Benefits of Microservices**

```
âœ… Scalability      - Scale only the service that needs it
âœ… Flexibility      - Use different tech for different services
âœ… Resilience       - One service failure doesn't crash everything
âœ… Speed            - Independent teams work faster
âœ… Easier Testing   - Test one service in isolation
âœ… Easy Deployment  - Deploy service A without touching service B
âœ… Technology Mix   - Auth in Django, Orders in Node.js, etc.
```

### **Challenges of Microservices**

```
âš ï¸  Complexity       - Managing multiple services is harder
âš ï¸  Network Latency  - Services call each other over network
âš ï¸  Data Consistency - Distributed transactions are tricky
âš ï¸  Debugging        - Bugs span multiple services
âš ï¸  DevOps Overhead  - Need Docker, K8s, monitoring
âš ï¸  Testing          - Integration tests are harder
```

---

## Microservices vs Monolithic Architecture

### **Monolithic Architecture**

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚       MONOLITHIC APPLICATION            â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  Auth Module                    â”‚   â”‚
â”‚  â”‚  â”œâ”€ Login/Register              â”‚   â”‚
â”‚  â”‚  â”œâ”€ Token Management            â”‚   â”‚
â”‚  â”‚  â””â”€ User Model                  â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  Order Module                   â”‚   â”‚
â”‚  â”‚  â”œâ”€ Create Order                â”‚   â”‚
â”‚  â”‚  â”œâ”€ Update Order                â”‚   â”‚
â”‚  â”‚  â””â”€ Order Model                 â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  Payment Module                 â”‚   â”‚
â”‚  â”‚  â”œâ”€ Process Payment             â”‚   â”‚
â”‚  â”‚  â”œâ”€ Refund                      â”‚   â”‚
â”‚  â”‚  â””â”€ Payment Model               â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                                         â”‚
â”‚  ONE DATABASE                           â”‚
â”‚  â””â”€ Shared tables: users, orders, ... â”‚
â”‚                                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Deploy: All modules together
Scale: Scale entire app even if only Orders is busy
```

### **Microservices Architecture**

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              API GATEWAY (Router)                    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤

       â”‚                â”‚                â”‚
       â–¼                â–¼                â–¼

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ AUTH SERVICE â”‚  â”‚ORDER SERVICE â”‚  â”‚PAYMENT SVCE  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚              â”‚  â”‚              â”‚  â”‚              â”‚
â”‚Login/Registerâ”‚  â”‚Create Order  â”‚  â”‚Process Pay   â”‚
â”‚Token MFT     â”‚  â”‚Update Order  â”‚  â”‚Refund        â”‚
â”‚              â”‚  â”‚              â”‚  â”‚              â”‚
â”‚DB: users     â”‚  â”‚DB: orders    â”‚  â”‚DB: payments  â”‚
â”‚              â”‚  â”‚              â”‚  â”‚              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Deploy: Separately
Scale: Only Orders service if needed
```

### **Comparison Table**

| Factor | Monolithic | Microservices |
|--------|-----------|---------------|
| **Deployment** | All or nothing | Individual services |
| **Scaling** | Entire app | Individual services |
| **Technology** | One stack | Multiple stacks |
| **Database** | Shared database | Database per service |
| **Team Size** | Large, coordinated | Small, independent |
| **Testing** | Integrated | Isolated + Integration |
| **Latency** | Low (in-process) | Higher (network calls) |
| **Complexity** | Lower | Higher (DevOps) |
| **Best For** | Small-medium apps | Large, complex apps |

---

## Real_MFA as a Microservice

### ðŸŽ¯ **Why Real_MFA is Perfect as Microservice**

Real_MFA is **already designed as a standalone microservice**:

```python
âœ… Independent API        - Doesn't require other services
âœ… Own Database          - Completely separate from business application
âœ… Own Dependencies      - Celery, Redis, PostgreSQL
âœ… REST Endpoints        - All communication via HTTP
âœ… Stateless Auth        - JWT tokens, no session coupling
âœ… Containerizable       - Docker-ready code
âœ… Scalable              - Horizontal scaling with Celery workers
âœ… Reusable              - Used by any application
```

### **Real_MFA in System Architecture**

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    APP CLIENT                               â”‚
â”‚              (Web Browser / Mobile App)                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
         â”‚                                             â”‚
         â–¼                                             â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚    API GATEWAY               â”‚          â”‚   REAL_MFA SERVICE  â”‚
â”‚  (Kong/AWS API Gateway)      â”‚          â”‚   (Microservice)    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤          â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Routes /api/orders â†’ Orders â”‚          â”‚ â€¢ Login/Register    â”‚
â”‚  Routes /api/auth â†’ REAL_MFA â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚ â€¢ MFA/TOTP          â”‚
â”‚  Routes /api/payment â†’ Pay   â”‚          â”‚ â€¢ Device Mgmt       â”‚
â”‚                              â”‚          â”‚ â€¢ Audit Logs        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚                                        â”‚
         â–¼                                        â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚    ECOMMERCE SERVICE         â”‚          â”‚  AUTH DATABASE      â”‚
â”‚  â€¢ Orders                    â”‚          â”‚  (PostgreSQL)       â”‚
â”‚  â€¢ Products                  â”‚          â”‚                     â”‚
â”‚  â€¢ Inventory                 â”‚          â”‚  Tables:            â”‚
â”‚                              â”‚          â”‚  - users            â”‚
â”‚    DB:                       â”‚          â”‚  - profiles         â”‚
â”‚    - customers               â”‚          â”‚  - devices          â”‚
â”‚    - orders                  â”‚          â”‚  - sessions         â”‚
â”‚    - products                â”‚          â”‚  - audit_logs       â”‚
â”‚    - inventory               â”‚          â”‚  - otps             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## How to Deploy Real_MFA as Microservice

### **Step 1: Prepare Environment**

#### **1.1 Database Setup (PostgreSQL)**

```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database for Real_MFA
createdb real_mfa_db

# Create user
psql -U postgres -d real_mfa_db
# In psql:
# CREATE USER mfa_user WITH PASSWORD 'strong_password';
# ALTER ROLE mfa_user SET client_encoding TO 'utf8';
# GRANT ALL PRIVILEGES ON DATABASE real_mfa_db TO mfa_user;
```

#### **1.2 Update settings.py**

```python
# Real_MFA/settings.py

import os
from pathlib import Path

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'real_mfa_db'),
        'USER': os.getenv('DB_USER', 'mfa_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'strong_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Security Settings (Production)
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# CORS for Ecommerce App
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Frontend
    "http://localhost:8080",
    "https://ecommerce.example.com",
]
```

### **Step 2: Create .env File**

```bash
# Real_MFA/.env

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,auth.example.com

# Database
DB_ENGINE=postgresql
DB_NAME=real_mfa_db
DB_USER=mfa_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend
FRONTEND_URL=http://localhost:3000
```

### **Step 3: Create Dockerfile**

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY Real_MFA/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/')"

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "Real_MFA.wsgi:application"]
```

### **Step 4: Docker Compose Setup**

```yaml
# docker-compose.yml

version: '3.9'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: real_mfa_db
    environment:
      POSTGRES_DB: real_mfa_db
      POSTGRES_USER: mfa_user
      POSTGRES_PASSWORD: strong_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mfa_user -d real_mfa_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: real_mfa_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Real_MFA API Service
  real_mfa:
    build: ./real_mfa
    container_name: real_mfa_api
    command: >
      sh -c "python manage.py migrate &&
             gunicorn --bind 0.0.0.0:8000 --workers 4 Real_MFA.wsgi:application"
    ports:
      - "8000:8000"
    environment:
      DEBUG: "False"
      DATABASE_URL: postgresql://mfa_user:strong_password@postgres:5432/real_mfa_db
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      FRONTEND_URL: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./real_mfa:/app
    networks:
      - mfa_network

  # Celery Worker (Async Tasks)
  celery_worker:
    build: ./real_mfa
    container_name: real_mfa_celery
    command: celery -A Real_MFA worker -l info --concurrency=4
    environment:
      DEBUG: "False"
      DATABASE_URL: postgresql://mfa_user:strong_password@postgres:5432/real_mfa_db
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      EMAIL_HOST_PASSWORD: ${EMAIL_HOST_PASSWORD}
    depends_on:
      - postgres
      - redis
    networks:
      - mfa_network

  # Celery Beat (Scheduler)
  celery_beat:
    build: ./real_mfa
    container_name: real_mfa_beat
    command: celery -A Real_MFA beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      DEBUG: "False"
      DATABASE_URL: postgresql://mfa_user:strong_password@postgres:5432/real_mfa_db
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - mfa_network

  # API Gateway (Optional - Kong/Nginx)
  nginx:
    image: nginx:latest
    container_name: api_gateway
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - real_mfa
    networks:
      - mfa_network

volumes:
  postgres_data:

networks:
  mfa_network:
    driver: bridge
```

### **Step 5: Run the Microservice**

```bash
# Navigate to project directory
cd Real_MFA

# Build and start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f real_mfa

# Stop services
docker-compose down
```

### **Step 6: Verify Real_MFA is Running**

```bash
# Test the API
curl http://localhost:8000/api/health/

# Expected Response:
# {"status": "ok", "database": "connected"}

# Test registration
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "device": {"fingerprint_hash": "abc123"}
  }'
```

---

## Reusability Across Projects

### ðŸ”„ **How Real_MFA is Reusable**

Real_MFA is **100% reusable** because it:

1. **Has no business logic** - Only handles authentication
2. **Uses REST API** - Language-agnostic communication
3. **Returns JWT tokens** - Standard format, easy integration
4. **Independent database** - Doesn't pollute your app's DB
5. **Docker-ready** - Deploy anywhere (local, cloud, K8s)

### **Real_MFA Works With Any Project**

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Real_MFA (Django)                                     â”‚
â”‚  Port 8000                                             â”‚
â”‚                                                        â”‚
â”‚  Provides:                                             â”‚
â”‚  - User registration/login                            â”‚
â”‚  - JWT tokens                                         â”‚
â”‚  - MFA/TOTP                                           â”‚
â”‚  - Device management                                  â”‚
â”‚  - Audit logging                                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â–²                      â–²                â–²
         â”‚                      â”‚                â”‚
         â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
         â”‚                      â”‚                â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”       â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”
    â”‚ ECOMMERCE â”‚       â”‚ BLOG      â”‚    â”‚ SOCIAL MEDIAâ”‚
    â”‚ (Node.js) â”‚       â”‚ (Python)  â”‚    â”‚ (Go)        â”‚
    â”‚ Port 3000 â”‚       â”‚ Port 4000 â”‚    â”‚ Port 5000   â”‚
    â”‚           â”‚       â”‚           â”‚    â”‚             â”‚
    â”‚ Uses JWT  â”‚       â”‚ Uses JWT  â”‚    â”‚ Uses JWT    â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜       â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
         â”‚                     â”‚                â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              All use same Real_MFA service
              All use same user accounts
              All track in same audit logs
```

### **Use Case 1: Ecommerce + Blog**

```
Customer registers on ecommerce.com
â†“ (via Real_MFA)
email: customer@example.com
password_hash: ****
â†“
Gets JWT token
â†“
Login to blog.com with same account
â†“ (Real_MFA validates token)
Single Sign-On (SSO) achieved!
```

### **Use Case 2: Multiple Websites**

```
Real_MFA Serves:
â”œâ”€â”€ Website A (Corporate)
â”œâ”€â”€ Website B (Ecommerce)
â”œâ”€â”€ Website C (SaaS)
â”œâ”€â”€ Mobile App (Native)
â””â”€â”€ Admin Dashboard

All users:
- Register once at Real_MFA
- All 5 applications recognize them
- One audit trail for all
```

---

## Handling Different Account Models

### â“ **The Problem**

Different projects need different user fields:

```
ECOMMERCE PROJECT:
â”œâ”€ username
â”œâ”€ email
â”œâ”€ password
â”œâ”€ phone_number
â””â”€ billing_address

BLOG PROJECT:
â”œâ”€ username
â”œâ”€ email
â”œâ”€ password
â””â”€ bio

SAAS PROJECT:
â”œâ”€ username
â”œâ”€ email
â”œâ”€ password
â”œâ”€ company_name
â”œâ”€ subscription_tier
â””â”€ billing_info
```

**Question:** Real_MFA User model has `email`, `username`, `phone_number`, etc. What if ecommerce needs more fields like `billing_address`, `company_name`, etc.?

### âœ… **Solution: User Extension Pattern**

Don't modify Real_MFA's User model. Instead, **extend it in your application**:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Real_MFA SERVICE               â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ User Model (Core Fields)         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€-â”¤
â”‚ â”œâ”€ id (UUID)                     â”‚
â”‚ â”œâ”€ email                         â”‚
â”‚ â”œâ”€ username                      â”‚
â”‚ â”œâ”€ password_hash                 â”‚
â”‚ â”œâ”€ phone_number                  â”‚
â”‚ â”œâ”€ email_verified                â”‚
â”‚ â”œâ”€ mfa_enabled                   â”‚
â”‚ â”œâ”€ created_at                    â”‚
â”‚ â””â”€ updated_at                    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ (JWT token + user_id)
         â”‚
       â”Œâ”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚                            â”‚
    â”Œâ”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
    â”‚ ECOMMERCE APP   â”‚   â”‚ BLOG APP      â”‚
    â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤   â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
    â”‚ EcomUser model: â”‚   â”‚ BlogUser      â”‚
    â”‚                 â”‚   â”‚ model:        â”‚
    â”‚ user_id (FK)    â”‚   â”‚               â”‚
    â”‚ billing_addr    â”‚   â”‚ user_id (FK)  â”‚
    â”‚ shipping_addr   â”‚   â”‚ bio           â”‚
    â”‚ company_name    â”‚   â”‚ website_url   â”‚
    â”‚ phone_number    â”‚   â”‚ social_links  â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### **Implementation: Extending User Model**

#### **Step 1: Create Custom User Profile in Each App**

```python
# ecommerce/models.py

from django.db import models
import uuid

class EcommerceUser(models.Model):
    """Extended user profile for ecommerce app"""

    # Reference to Real_MFA user (not storing duplicate data)
    user_id = models.UUIDField(unique=True, db_index=True)  # From Real_MFA JWT
    email = models.EmailField(unique=True)  # Cache for queries

    # Ecommerce-specific fields
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    # Preferences
    default_currency = models.CharField(max_length=3, default='USD')
    language = models.CharField(max_length=10, default='en')
    newsletter_subscribed = models.BooleanField(default=True)

    # Loyalty
    loyalty_points = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ecommerce_users'

    def __str__(self):
        return self.email
```

```python
# blog/models.py

from django.db import models
import uuid

class BlogUser(models.Model):
    """Extended user profile for blog app"""

    user_id = models.UUIDField(unique=True, db_index=True)
    email = models.EmailField(unique=True)

    # Blog-specific fields
    bio = models.TextField(blank=True, max_length=500)
    profile_picture = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    # Social Links
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)

    # Settings
    posts_per_page = models.PositiveIntegerField(default=10)
    theme = models.CharField(
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_users'

    def __str__(self):
        return self.email
```

#### **Step 2: When User Registers, Create Extended Profile**

```python
# ecommerce/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import EcommerceUser

@api_view(['POST'])
@permission_classes([AllowAny])
def register_ecommerce_user(request):
    """
    1. Register user at Real_MFA
    2. Create extended profile in ecommerce
    """

    # Call Real_MFA registration API
    real_mfa_url = 'http://localhost:8000/api/auth/register/'

    response = requests.post(real_mfa_url, json={
        'username': request.data['username'],
        'email': request.data['email'],
        'password': request.data['password'],
        'password2': request.data['password2'],
        'device': request.data.get('device', {})
    })

    if response.status_code != 201:
        return Response(response.json(), status=response.status_code)

    # Real_MFA response
    user_data = response.json()
    user_id = user_data['id']
    email = user_data['email']

    # Create extended profile in ecommerce database
    try:
        ecom_user = EcommerceUser.objects.create(
            user_id=user_id,
            email=email,
            default_currency=request.data.get('currency', 'USD'),
            language=request.data.get('language', 'en')
        )

        return Response({
            'status': 'success',
            'message': 'User registered successfully',
            'user_id': str(user_id),
            'email': email
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Error creating profile: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
```

#### **Step 3: When User Logs In, Link JWT to Extended Profile**

```python
# ecommerce/middleware.py or views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests
from .models import EcommerceUser
from rest_framework_simplejwt.authentication import JWTAuthentication

@api_view(['POST'])
@permission_classes([AllowAny])
def login_ecommerce_user(request):
    """
    1. Login at Real_MFA
    2. Get JWT token + user_id
    3. Find extended profile
    4. Return enhanced response
    """

    # Call Real_MFA login API
    real_mfa_url = 'http://localhost:8000/api/auth/login/'

    response = requests.post(real_mfa_url, json={
        'identifier': request.data['email'],
        'password': request.data['password'],
        'device': request.data.get('device', {})
    })

    if response.status_code not in [200, 202]:
        return Response(response.json(), status=response.status_code)

    login_data = response.json()
    user_id = login_data['user']['id']

    # Try to find extended profile
    try:
        ecom_user = EcommerceUser.objects.get(user_id=user_id)

        # Add ecommerce-specific data to response
        login_data['ecommerce'] = {
            'loyalty_points': ecom_user.loyalty_points,
            'total_spent': str(ecom_user.total_spent),
            'currency': ecom_user.default_currency,
            'newsletter': ecom_user.newsletter_subscribed
        }

    except EcommerceUser.DoesNotExist:
        # Create profile if doesn't exist (shouldn't happen if registered normally)
        EcommerceUser.objects.create(
            user_id=user_id,
            email=login_data['user']['email']
        )

    return Response(login_data, status=response.status_code)
```

#### **Step 4: Middleware to Validate JWT and Load Extended Profile**

```python
# ecommerce/middleware.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import EcommerceUser
from django.utils.decorators import decorator_from_middleware
from django.middleware.common import CommonMiddleware

class JWTtoEcomUserMiddleware:
    """
    Middleware that:
    1. Validates JWT token from Real_MFA
    2. Loads extended EcommerceUser profile
    3. Attaches to request
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract JWT from headers
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer '

            try:
                # Validate with Real_MFA
                jwt_auth = JWTAuthentication()
                validated = jwt_auth.get_validated_token(token)
                user_id = validated['user_id']

                # Load extended profile
                ecom_user = EcommerceUser.objects.get(user_id=user_id)
                request.ecom_user = ecom_user
                request.user_id = user_id

            except Exception as e:
                # Token invalid or user not found
                request.ecom_user = None

        response = self.get_response(request)
        return response

# Add to settings.py MIDDLEWARE:
# 'ecommerce.middleware.JWTtoEcomUserMiddleware',
```

---

## Implementation Examples

### **Example 1: Ecommerce Registration**

**Flow:**
```
Customer Registration
â†“
POST /api/register (Ecommerce)
â”œâ”€ Call Real_MFA: POST /api/auth/register/
â”œâ”€ Real_MFA creates user, sends verification email
â”œâ”€ Ecommerce creates EcommerceUser profile
â””â”€ Return success to client
```

**Code:**
```python
# ecommerce/serializers.py

from rest_framework import serializers
import requests

class EcommerceRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(required=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        # 1. Register at Real_MFA
        real_mfa_response = requests.post(
            'http://real_mfa:8000/api/auth/register/',
            json={
                'username': validated_data['username'],
                'email': validated_data['email'],
                'password': validated_data['password'],
                'password2': validated_data['password2'],
                'phone_number': validated_data.get('phone', ''),
                'device': {
                    'fingerprint_hash': self.context['request'].data.get('device_hash', '')
                }
            }
        )

        if real_mfa_response.status_code != 201:
            raise serializers.ValidationError(real_mfa_response.json())

        user_data = real_mfa_response.json()

        # 2. Create ecommerce profile
        from .models import EcommerceUser
        ecom_user = EcommerceUser.objects.create(
            user_id=user_data['id'],
            email=user_data['email']
        )

        return {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'message': 'Verify your email to complete registration'
        }
```

### **Example 2: Ecommerce Login with MFA**

**Flow:**
```
Customer Login
â†“
POST /api/login (Ecommerce)
â”œâ”€ Call Real_MFA: POST /api/auth/login/
â”œâ”€ Check MFA required?
â”‚  â”œâ”€ YES: Return mfa_required, wait for TOTP
â”‚  â””â”€ NO: Proceed
â”œâ”€ Load EcommerceUser profile
â”œâ”€ Add loyalty points, cart data
â””â”€ Return tokens + ecommerce data
```

**Code:**
```python
# ecommerce/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from .models import EcommerceUser
from django.core.cache import cache

@api_view(['POST'])
def login(request):
    email = request.data['email']
    password = request.data['password']

    # 1. Authenticate at Real_MFA
    real_mfa_response = requests.post(
        'http://real_mfa:8000/api/auth/login/',
        json={
            'identifier': email,
            'password': password,
            'device': request.data.get('device', {})
        }
    )

    login_data = real_mfa_response.json()

    # Check if MFA required
    if login_data.get('status') == 'mfa_required':
        # Cache user_id for MFA verification
        cache.set(
            f"mfa_pending:{login_data['user_id']}",
            login_data,
            timeout=900  # 15 minutes
        )
        return Response(login_data, status=202)

    # 2. User fully authenticated - get JWT tokens
    user_id = login_data['user']['id']

    # 3. Load ecommerce profile
    ecom_user = EcommerceUser.objects.get(user_id=user_id)

    # 4. Enhance response with ecommerce data
    login_data['commerce'] = {
        'loyalty_points': ecom_user.loyalty_points,
        'total_spent': str(ecom_user.total_spent),
        'vip_status': ecom_user.total_spent > 10000,
    }

    return Response(login_data)
```

### **Example 3: BlogUser with Extended Profile**

```python
# blog/serializers.py

from rest_framework import serializers
import requests
from .models import BlogUser

class BlogRegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    bio = serializers.CharField(required=False)

    def create(self, validated_data):
        # Register at Real_MFA
        real_mfa_response = requests.post(
            'http://real_mfa:8000/api/auth/register/',
            json={
                'username': validated_data['username'],
                'email': validated_data['email'],
                'password': validated_data['password'],
                'password2': validated_data['password2'],
                'device': self.context['request'].data.get('device', {})
            }
        )

        if real_mfa_response.status_code != 201:
            raise serializers.ValidationError(real_mfa_response.json())

        user_data = real_mfa_response.json()

        # Create blog profile
        blog_user = BlogUser.objects.create(
            user_id=user_data['id'],
            email=user_data['email'],
            bio=validated_data.get('bio', '')
        )

        return blog_user
```

### **Example 4: Django SaaS Project (Solo App)**

**Scenario:** You have a Django SaaS application (like Trello clone, Project Manager, etc.) that needs authentication and want to use Real_MFA.

**Models:**
```python
# saas/models.py

from django.db import models
import uuid

class SaaSUser(models.Model):
    """Extended user profile for SaaS application"""

    user_id = models.UUIDField(unique=True, db_index=True)
    email = models.EmailField(unique=True)

    # SaaS-specific fields
    company_name = models.CharField(max_length=255, blank=True)
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free - 1 project'),
            ('pro', 'Pro - 5 projects'),
            ('enterprise', 'Enterprise - Unlimited projects')
        ],
        default='free'
    )
    subscription_active = models.BooleanField(default=False)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)

    # API Access
    api_key = models.CharField(max_length=255, unique=True, blank=True)
    api_key_created_at = models.DateTimeField(null=True, blank=True)

    # Team/Organization
    team_members_count = models.PositiveIntegerField(default=1)
    is_team_owner = models.BooleanField(default=True)

    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    notifications_enabled = models.BooleanField(default=True)

    # Limits
    projects_created = models.PositiveIntegerField(default=0)
    max_projects = models.PositiveIntegerField(default=1)  # Based on tier

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saas_users'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['subscription_tier']),
            models.Index(fields=['subscription_active']),
        ]

    def __str__(self):
        return self.email

    def can_create_project(self):
        """Check if user can create more projects"""
        return self.projects_created < self.max_projects

    def upgrade_subscription(self, tier):
        """Upgrade subscription tier"""
        tier_limits = {
            'free': 1,
            'pro': 5,
            'enterprise': 999
        }
        self.subscription_tier = tier
        self.max_projects = tier_limits.get(tier, 1)
        self.subscription_active = True
        self.save()


class Project(models.Model):
    """Projects owned by SaaS users"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(SaaSUser, on_delete=models.CASCADE, related_name='projects')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Settings
    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
```

**Registration:**
```python
# saas/serializers.py

from rest_framework import serializers
import requests
from .models import SaaSUser
import secrets

class SaaSRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    company_name = serializers.CharField(max_length=255, required=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        """Register at Real_MFA and create SaaS profile"""

        # 1. Register at Real_MFA
        real_mfa_response = requests.post(
            'http://real_mfa:8000/api/auth/register/',
            json={
                'username': validated_data['username'],
                'email': validated_data['email'],
                'password': validated_data['password'],
                'password2': validated_data['password2'],
                'device': self.context['request'].data.get('device', {})
            }
        )

        if real_mfa_response.status_code != 201:
            raise serializers.ValidationError(real_mfa_response.json())

        user_data = real_mfa_response.json()

        # 2. Create SaaS profile
        saas_user = SaaSUser.objects.create(
            user_id=user_data['id'],
            email=user_data['email'],
            company_name=validated_data.get('company_name', ''),
            subscription_tier='free',
            max_projects=1,
            api_key=f"sk_{secrets.token_urlsafe(32)}"  # Generate API key
        )

        return {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'company_name': saas_user.company_name,
            'subscription_tier': saas_user.subscription_tier,
            'message': 'Welcome to SaaS! Verify your email to get started.'
        }
```

**Login with Authorization Checks:**
```python
# saas/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import SaaSUser, Project
from django.core.cache import cache

@api_view(['POST'])
def login_saas(request):
    """
    Login to SaaS with Real_MFA validation
    Returns subscription info and team details
    """

    email = request.data['email']
    password = request.data['password']

    # Authenticate at Real_MFA
    real_mfa_response = requests.post(
        'http://real_mfa:8000/api/auth/login/',
        json={
            'identifier': email,
            'password': password,
            'device': request.data.get('device', {})
        }
    )

    if real_mfa_response.status_code not in [200, 202]:
        return Response(real_mfa_response.json(), status=real_mfa_response.status_code)

    login_data = real_mfa_response.json()

    # Check MFA
    if login_data.get('status') == 'mfa_required':
        cache.set(
            f"saas_mfa:{login_data['user_id']}",
            login_data,
            timeout=900
        )
        return Response(login_data, status=202)

    # User authenticated
    user_id = login_data['user']['id']

    # Load SaaS profile
    saas_user = SaaSUser.objects.get(user_id=user_id)

    # Check subscription status
    if not saas_user.subscription_active and saas_user.subscription_tier != 'free':
        return Response({
            'error': 'Subscription expired',
            'user_id': str(user_id),
            'subscription_expired': True
        }, status=402)

    # Enhance response with SaaS data
    login_data['saas'] = {
        'company_name': saas_user.company_name,
        'subscription_tier': saas_user.subscription_tier,
        'projects_count': saas_user.projects.count(),
        'team_members': saas_user.team_members_count,
        'can_create_project': saas_user.can_create_project(),
        'api_key': saas_user.api_key
    }

    return Response(login_data, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    """
    Create new project with authorization checks
    Requires: Valid JWT + subscription allows projects
    """

    # Extract user_id from JWT
    user_id = request.user.id  # From middleware

    # Get SaaS user
    saas_user = SaaSUser.objects.get(user_id=user_id)

    # Check if can create more projects
    if not saas_user.can_create_project():
        return Response({
            'error': f'Project limit reached for {saas_user.subscription_tier} tier',
            'current': saas_user.projects_created,
            'max': saas_user.max_projects,
            'upgrade_required': True
        }, status=403)

    # Create project
    project = Project.objects.create(
        owner=saas_user,
        name=request.data['name'],
        description=request.data.get('description', '')
    )

    saas_user.projects_created += 1
    saas_user.save(update_fields=['projects_created'])

    return Response({
        'id': str(project.id),
        'name': project.name,
        'owner_id': str(saas_user.user_id),
        'created_at': project.created_at
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_projects(request):
    """List all projects for authenticated user"""

    user_id = request.user.id
    saas_user = SaaSUser.objects.get(user_id=user_id)

    projects = saas_user.projects.all().values('id', 'name', 'description', 'is_public', 'created_at')

    return Response({
        'user': {
            'email': saas_user.email,
            'subscription_tier': saas_user.subscription_tier,
            'company': saas_user.company_name
        },
        'projects': list(projects),
        'count': saas_user.projects.count()
    })
```

**Settings Configuration:**
```python
# saas/settings.py

# Real_MFA Configuration
REAL_MFA_URL = os.getenv('REAL_MFA_URL', 'http://localhost:8000')

# Database (SaaS-specific)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'saas_db'),
        'USER': os.getenv('DB_USER', 'saas_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis for caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    }
}

# JWT - Use Real_MFA's tokens
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# API throttling
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'user': '1000/hour',
    'anon': '100/hour'
}
```

**Stripe Subscription Integration:**
```python
# saas/integrations/stripe_handler.py

import stripe
from ..models import SaaSUser
from django.utils import timezone
from datetime import timedelta

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class SubscriptionManager:

    @staticmethod
    def upgrade_to_pro(user_id, stripe_token):
        """Upgrade SaaS user to Pro tier"""

        saas_user = SaaSUser.objects.get(user_id=user_id)

        try:
            # Create Stripe charge
            charge = stripe.Charge.create(
                amount=9900,  # $99.00
                currency='usd',
                source=stripe_token,
                description=f'Pro subscription for {saas_user.email}'
            )

            # Update subscription
            saas_user.subscription_tier = 'pro'
            saas_user.subscription_active = True
            saas_user.subscription_expires_at = timezone.now() + timedelta(days=365)
            saas_user.max_projects = 5
            saas_user.save()

            return {
                'status': 'success',
                'tier': 'pro',
                'expires_at': saas_user.subscription_expires_at,
                'projects_available': saas_user.max_projects
            }

        except stripe.error.CardError as e:
            return {
                'status': 'failed',
                'error': e.user_message
            }
```

**Middleware for JWT to SaaSUser Linking:**
```python
# saas/middleware.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import SaaSUser
from django.utils.decorators import decorator_from_middleware

class JWTToSaaSUserMiddleware:
    """
    Validates JWT with Real_MFA and links to SaaSUser
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

            try:
                jwt_auth = JWTAuthentication()
                validated = jwt_auth.get_validated_token(token)
                user_id = validated.get('user_id')

                # Link to SaaSUser
                saas_user = SaaSUser.objects.get(user_id=user_id)
                request.user = saas_user
                request.user_id = user_id
                request.is_authenticated = True

            except Exception as e:
                request.is_authenticated = False
                request.user = None

        response = self.get_response(request)
        return response

# Add to settings.py:
# MIDDLEWARE = [
#     ...
#     'saas.middleware.JWTToSaaSUserMiddleware',
# ]
```

**URL Configuration:**
```python
# saas/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('auth/login/', views.login_saas, name='saas-login'),
    path('auth/register/', views.register_saas_user, name='saas-register'),

    # Projects
    path('projects/', views.list_projects, name='list-projects'),
    path('projects/create/', views.create_project, name='create-project'),
    path('projects/<uuid:project_id>/', views.get_project, name='get-project'),
    path('projects/<uuid:project_id>/delete/', views.delete_project, name='delete-project'),

    # Subscription
    path('subscription/upgrade/', views.upgrade_subscription, name='upgrade-subscription'),
    path('subscription/status/', views.get_subscription_status, name='subscription-status'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel-subscription'),

    # API Keys
    path('api-keys/generate/', views.generate_api_key, name='generate-api-key'),
    path('api-keys/list/', views.list_api_keys, name='list-api-keys'),
    path('api-keys/revoke/', views.revoke_api_key, name='revoke-api-key'),
]

# In main urls.py
# path('api/saas/', include('saas.urls')),
```

**Complete Architecture:**
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚         SaaS Frontend (React/Vue)            â”‚
â”‚         (Dashboard, Project Editor)          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚           â”‚           â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”  â”Œâ”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”
    â”‚Register â”‚  â”‚ Login  â”‚  â”‚Project   â”‚
    â”‚/ Login  â”‚  â”‚+ MFA   â”‚  â”‚CRUD      â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”¬â”€â”€â”€â”€â”˜  â””â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚           â”‚           â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚
                â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”
                â”‚ SaaS Django â”‚
                â”‚  API        â”‚
                â”‚ (Port 3000) â”‚
                â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚           â”‚             â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚Real_MFA â”‚  â”‚SaaS DB   â”‚  â”‚Stripe API   â”‚
    â”‚(Auth)   â”‚  â”‚(Projects)â”‚  â”‚(Payments)   â”‚
    â”‚Port8000 â”‚  â”‚Postgres  â”‚  â”‚             â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

All authentication flows through Real_MFA
SaaS DB stores only business logic (projects, teams, subscriptions)
```

---

## Best Practices

### 1ï¸âƒ£ **Always Use Real_MFA for Authentication**

```python
# âœ… CORRECT
# Validate JWT with Real_MFA
response = requests.get(
    'http://real_mfa:8000/api/profile/me/',
    headers={'Authorization': f'Bearer {token}'}
)

# âŒ AVOID
# Don't try to validate JWT yourself
# Don't create your own user table with password
```

### 2ï¸âƒ£ **Cache User Data Locally**

```python
# Good Practice: Cache extended profile
from django.core.cache import cache

def get_ecom_user(user_id):
    # Check cache first
    cached = cache.get(f'ecom_user:{user_id}')
    if cached:
        return cached

    # Fetch from DB if not cached
    user = EcommerceUser.objects.get(user_id=user_id)
    cache.set(f'ecom_user:{user_id}', user, timeout=3600)  # 1 hour
    return user
```

### 3ï¸âƒ£ **Handle Real_MFA Downtime Gracefully**

```python
# Graceful degradation
import requests
from requests.exceptions import ConnectionError

def get_user_from_jwt(token):
    try:
        response = requests.get(
            'http://real_mfa:8000/api/profile/me/',
            headers={'Authorization': f'Bearer {token}'},
            timeout=5  # Don't wait forever
        )
        return response.json() if response.status_code == 200 else None

    except ConnectionError:
        # Real_MFA is down
        # Check if we have cached user data
        logger.error("Real_MFA service unavailable")
        return None

    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        return None
```

### 4ï¸âƒ£ **Implement Service-to-Service Authentication**

```python
# For service-to-service calls (not user-facing)

# In Real_MFA, create an API key for ecommerce
# ecommerce/config.py

REAL_MFA_SERVICE = {
    'URL': 'http://real_mfa:8000',
    'API_KEY': os.getenv('REAL_MFA_API_KEY'),  # Shared secret
}

# When calling Real_MFA from ecommerce
import hmac
import hashlib

def call_real_mfa(endpoint, data=None, method='GET'):
    timestamp = int(time.time())

    # Create signature
    message = f"{endpoint}:{timestamp}".encode()
    signature = hmac.new(
        REAL_MFA_SERVICE['API_KEY'].encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    headers = {
        'X-API-Key': REAL_MFA_SERVICE['API_KEY'],
        'X-Timestamp': str(timestamp),
        'X-Signature': signature
    }

    url = f"{REAL_MFA_SERVICE['URL']}{endpoint}"

    if method == 'GET':
        return requests.get(url, headers=headers)
    elif method == 'POST':
        return requests.post(url, json=data, headers=headers)
```

### 5ï¸âƒ£ **Database Sync Strategy**

```python
# Option 1: Cache-based (Recommended for most cases)
# 1. User registers at Real_MFA
# 2. Ecommerce gets user_id from JWT
# 3. Ecommerce creates local profile
# 4. Always validate JWT before accepting requests

# Option 2: Event-based (For complex scenarios)
# 1. Real_MFA sends webhook when user registers
# 2. Ecommerce receives webhook and creates profile
# 3. Both stay in sync via events

# Webhook handler in ecommerce
@api_view(['POST'])
def webhook_user_registered(request):
    """Handle Real_MFA user registration webhook"""

    event_data = request.data

    if event_data['event'] == 'user.registered':
        user_id = event_data['user_id']
        email = event_data['email']

        EcommerceUser.objects.get_or_create(
            user_id=user_id,
            defaults={'email': email}
        )

    return Response({'status': 'received'})
```

### 6ï¸âƒ£ **Centralized User Data (Best Practice)**

```python
# Keep one source of truth
# Architecture:
#
# Real_MFA (Source of Truth)
# â”œâ”€ email
# â”œâ”€ password (hashed)
# â”œâ”€ phone_number
# â”œâ”€ mfa_enabled
# â””â”€ created_at
#
# Ecommerce (Extended Data)
# â”œâ”€ user_id (FK to Real_MFA)
# â”œâ”€ loyalty_points
# â”œâ”€ billing_address
# â””â”€ preferences
#
# Blog (Extended Data)
# â”œâ”€ user_id (FK to Real_MFA)
# â”œâ”€ bio
# â””â”€ social_links
#
# Principle: Never duplicate core data
```

---

## Troubleshooting

### **Issue 1: JWT Token Validation Fails**

```python
# Problem: Real_MFA service is down
# Token is returning 503

# Solution:
from django.core.exceptions import ImproperlyConfigured

def validate_jwt(token, fallback_cache=True):
    try:
        # Try to validate with Real_MFA
        response = requests.post(
            'http://real_mfa:8000/api/auth/validate-token/',
            json={'token': token},
            timeout=3
        )
        return response.status_code == 200

    except requests.exceptions.Timeout:
        # Real_MFA is slow
        logger.warning("Real_MFA timeout")

        if fallback_cache:
            # Check if we recently validated this token
            cached = cache.get(f'valid_token:{token_hash}')
            if cached:
                logger.warning("Using cached validation")
                return True

        raise AuthenticationFailed("Service temporarily unavailable")
```

### **Issue 2: Extended Profile Not Created**

```python
# Problem: User registered at Real_MFA but EcommerceUser doesn't exist

# Solution: Add retry logic
from django.core.management.base import BaseCommand
from .models import EcommerceUser
import requests

class Command(BaseCommand):
    def handle(self, *args, **options):
        """Sync missing profiles from Real_MFA"""

        # Get all Real_MFA users
        response = requests.get(
            'http://real_mfa:8000/api/admin/users/',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        real_mfa_users = response.json()['users']

        # Check which ones don't have ecommerce profile
        for user in real_mfa_users:
            ecom_user, created = EcommerceUser.objects.get_or_create(
                user_id=user['id'],
                defaults={'email': user['email']}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created profile for {user['email']}")
                )
```

### **Issue 3: Multiple Service Deployments (Different Versions)**

```python
# Problem: What if ecommerce and blog use different versions of Real_MFA?

# Solution: Version your API
# Real_MFA/settings.py
API_VERSION = 'v1'  # or 'v2'

# Ecommerce calls with version
requests.post(
    'http://real_mfa:8000/api/v1/auth/login/',
    json=data
)

# Blog calls with different version if needed
requests.post(
    'http://real_mfa:8000/api/v2/auth/login/',
    json=data
)
```

### **Issue 4: Database Consistency**

```python
# Problem: User updated email in Real_MFA
# Ecommerce still has old email cached

# Solution: Implement eventual consistency
def update_user_email(user_id, new_email):
    # 1. Update in Real_MFA
    requests.patch(
        f'http://real_mfa:8000/api/users/{user_id}/',
        json={'email': new_email}
    )

    # 2. Clear cache in ecommerce
    cache.delete(f'user:{user_id}')

    # 3. Update ecommerce profile
    EcommerceUser.objects.filter(user_id=user_id).update(
        email=new_email
    )
```

---

## Summary Table

| Aspect | Solution |
|--------|----------|
| **Different Account Fields** | Use extended profile model in each app |
| **User Identification** | Store Real_MFA user_id, not copying data |
| **Keeping Data in Sync** | Cache + periodic sync, or webhooks |
| **Service Failure** | Graceful degradation, timeout handling |
| **Multi-Project Deployment** | Containerize Real_MFA, use API Gateway |
| **Authentication** | Always validate JWT with Real_MFA |
| **Authorization** | Store role/permissions in extended profile |

---

## Conclusion

**Real_MFA is the perfect microservice because:**

1. âœ… **Stateless** - JWT tokens, no session coupling
2. âœ… **Reusable** - Works with any tech stack
3. âœ… **Scalable** - Horizontal scaling with multiple instances
4. âœ… **Independent** - Own database, own code
5. âœ… **Extensible** - Each app can extend User with custom fields
6. âœ… **Maintainable** - Single source of truth for auth

**All account differences are handled by extending the User model in each application, not by modifying Real_MFA.**

