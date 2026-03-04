# Real_MFA VPS Deployment Runbook (EC2 / Ubuntu)

This is a production-oriented, repeatable deployment flow for this project using Docker, PostgreSQL, Redis, Celery, Nginx, and GitHub Actions.

## 1) One-Time EC2 Setup

- Create Ubuntu 22.04 EC2 instance (minimum: 2 vCPU, 4GB RAM).
- Open security group ports: `22`, `80`, `443`.
- SSH in and run:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release git ufw fail2ban

# Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Firewall
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Use docker without sudo
sudo usermod -aG docker $USER
newgrp docker
```

## 2) Clone Project on Server

```bash
sudo mkdir -p /opt/real_mfa
sudo chown -R $USER:$USER /opt/real_mfa
cd /opt/real_mfa
git clone <your-repo-url> .
cd Real_MFA
```

## 3) Prepare Runtime Environment

```bash
cp .env.docker.example .env.docker
nano .env.docker
```

Required values in `.env.docker`:
- `ENVIRONMENT=production`
- `DEBUG=False`
- `SECRET_KEY=<strong-random-value>`
- `ALLOWED_HOSTS=<domain>,www.<domain>,<ec2-public-ip>`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DB_HOST=db`
- `REDIS_HOST=redis`
- `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` with your frontend/backend domains

## 4) First Manual Deploy (Smoke Test)

```bash
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml up -d --build
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml ps
curl -fsS http://127.0.0.1/healthz/
```

Create admin user:

```bash
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml exec web python manage.py createsuperuser
```

## 5) Domain + HTTPS

Recommended: put host Nginx in front of container Nginx or use ALB + ACM.
For fastest setup on VPS, install Certbot on host and terminate TLS on host Nginx forwarding to `127.0.0.1:80`.

## 6) GitHub Actions Secrets

Set these repository secrets:

- `SSH_HOST` = VPS public IP or domain
- `SSH_PORT` = `22`
- `SSH_USER` = ubuntu (or your user)
- `SSH_PRIVATE_KEY` = private key matching server authorized_keys
- `APP_PATH` = `/opt/real_mfa/Real_MFA`
- `GHCR_USERNAME` = GitHub username that can pull packages
- `GHCR_PAT` = Personal Access Token with `read:packages`

## 7) Deploy Flow

- Open PR -> `CI` runs Django checks + tests.
- Merge to `main` -> `Deploy to VPS` workflow builds image, pushes to GHCR, SSH deploys to VPS.
- Deploy workflow validates with `curl http://127.0.0.1/healthz/`.

## 8) Operations Best Practices

- Backups: schedule nightly PostgreSQL dumps + media backup.
- Monitoring: alert on `/healthz/` failure and container restarts.
- Rollback: redeploy previous image tag by setting `IMAGE` to earlier SHA.
- Security: rotate secrets regularly, disable password SSH login, keep OS patched.

## 9) Quick Troubleshooting

```bash
cd /opt/real_mfa/Real_MFA
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml logs -f web
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml logs -f celery_worker
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml logs -f db
docker compose --env-file .env.docker -f docker-compose.ubuntu.yml restart web
```
