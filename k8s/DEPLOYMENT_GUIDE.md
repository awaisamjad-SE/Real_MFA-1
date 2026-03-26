# Kubernetes Deployment Guide for Real_MFA

This guide explains how to deploy Real_MFA to DigitalOcean Kubernetes.

## Prerequisites

✅ You have:
- DigitalOcean K8s cluster running (v1.35.1)
- kubectl configured locally
- Docker Hub image: `awaisamjad1828/real_mfa:latest`

## Step 1: Prepare Secrets (IMPORTANT)

Secrets need to be base64 encoded before applying. Update `k8s/secret.yaml` with your actual values:

```bash
# Encode your values
echo -n "your-secret-value" | base64

# Example for Django SECRET_KEY
echo -n "your-django-secret-key" | base64
# Output: <BASE64_SECRET_KEY>

# Do the same for:
# - DB_PASSWORD (from your .env)
# - BREVO_API_KEY (from your .env)
# - REDIS_PASSWORD (create a strong one)
```

Then update these fields in `k8s/secret.yaml`:
- `SECRET_KEY`
- `DB_PASSWORD`
- `BREVO_API_KEY`
- `REDIS_PASSWORD` (add this if missing)

## Step 2: Apply Kubernetes Manifests

```bash
# Apply namespace first
kubectl apply -f k8s/namespace.yaml

# Apply config and secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Apply database (PostgreSQL)
kubectl apply -f k8s/postgres-statefulset.yaml

# Apply Redis
kubectl apply -f k8s/redis-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s -n real-mfa-prod

# Apply Django app
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Apply autoscaling
kubectl apply -f k8s/hpa.yaml

# Apply Ingress (requires nginx-ingress-controller)
kubectl apply -f k8s/ingress.yaml
```

## Step 3: Install Nginx Ingress Controller (if not already installed)

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

## Step 4: Install Cert-Manager (for SSL/TLS)

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

Then create ClusterIssuer for Let's Encrypt:

```bash
kubectl apply -f k8s/letsencrypt-issuer.yaml
```

## Step 5: Verify Deployment

```bash
# Check pod status
kubectl get pods -n real-mfa-prod

# Check services
kubectl get svc -n real-mfa-prod

# Check Ingress
kubectl get ingress -n real-mfa-prod

# View Ingress IP/hostname
kubectl get ingress -n real-mfa-prod -o wide

# Check HPA status
kubectl get hpa -n real-mfa-prod

# Verify app is running
kubectl logs -n real-mfa-prod -l app=real-mfa -c web --tail=50
kubectl logs -n real-mfa-prod -l app=real-mfa -c celery-worker --tail=50
```

## Step 6: Point DNS to Load Balancer

Get the external IP of the Loadbalancer:

```bash
kubectl get svc -n ingress-nginx
```

Point your domains to this IP:
- awaisamjad.engineer → [LOADBALANCER_IP]
- www.awaisamjad.engineer → [LOADBALANCER_IP]

## Step 7: Monitor Deployment

Check rolling updates:
```bash
kubectl rollout status deployment/real-mfa-web -n real-mfa-prod

# View rollout history
kubectl rollout history deployment/real-mfa-web -n real-mfa-prod

# Rollback if needed
kubectl rollout undo deployment/real-mfa-web -n real-mfa-prod
```

## Updating Deployment with New Image

When you push a new image to Docker Hub (via CI/CD), Kubernetes can auto-update:

```bash
# Manually trigger update (if ImagePullPolicy: Always and tag is latest)
kubectl rollout restart deployment/real-mfa-web -n real-mfa-prod

# Or update image tag
kubectl set image deployment/real-mfa-web web=awaisamjad1828/real_mfa:new-tag -n real-mfa-prod
```

## Debugging Tips

```bash
# Describe pod for detailed info
kubectl describe pod [pod-name] -n real-mfa-prod

# Check events
kubectl get events -n real-mfa-prod

# Port-forward to test locally
kubectl port-forward svc/real-mfa-web 8000:80 -n real-mfa-prod

# Exec into pod for debugging
kubectl exec -it [pod-name] -n real-mfa-prod -c web -- bash

# Check logs
kubectl logs [pod-name] -n real-mfa-prod -c web
kubectl logs [pod-name] -n real-mfa-prod -c celery-worker
```

## Troubleshooting

### Pods stuck in Pending
```bash
kubectl describe pod [pod-name] -n real-mfa-prod
# Check: resource limits, node availability, PVC binding
```

### ImagePullBackOff
- Verify Docker Hub image exists
- Check `imagePullSecrets` in deployment
- Verify credentials in secret

### Health check failing
- Check app is responding at `/healthz/`
- Verify database is ready
- Check logs: `kubectl logs [pod] -n real-mfa-prod`

### SSL certificate not issued
```bash
kubectl describe certificate real-mfa-tls -n real-mfa-prod
kubectl describe clusterissuer letsencrypt-prod
```

## Cost Optimization

- Use smaller node types for dev/staging
- Set appropriate resource limits to prevent runaway costs
- Use spot instances for non-critical workloads (DO offers this)
- Monitor pod resource usage regularly

## Next Steps

1. Enable monitoring with Prometheus + Grafana
2. Set up log aggregation (ELK stack or Loki)
3. Configure backup/restore strategies
4. Set up CI/CD to auto-deploy on Docker Hub push
5. Implement network policies for security
