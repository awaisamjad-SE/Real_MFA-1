# Kubernetes CI/CD Setup Guide for Real_MFA

This document explains how to connect your GitHub repository to your DigitalOcean Kubernetes cluster so GitHub Actions can auto-deploy.

## Architecture

```
Your Code (GitHub)
        ↓
    GitHub Actions (CI)
        ↓
    Build Docker Image
        ↓
    Push to Docker Hub (awaisamjad1828/real_mfa:latest)
        ↓
    GitHub Actions (CD for K8s)
        ↓
    kubectl apply (deploys to DO K8s cluster)
        ↓
    Kubernetes Rolling Update (zero downtime)
        ↓
    Your App is Live
```

---

## Step 1: Add GitHub Secrets

GitHub Actions needs access to your Kubernetes cluster. You'll add secrets to GitHub so the workflow can authenticate.

### 1.1 Get Your Kubeconfig

Your kubeconfig is already downloaded locally (when you ran `doctl kubernetes cluster kubeconfig save`).

Find it at:
```
C:\Users\awais\.kube\config
```

### 1.2 Encode Kubeconfig as Base64

GitHub Actions needs the kubeconfig in base64 format. PowerShell command:

```powershell
# Read and encode kubeconfig
$kubeconfigPath = "C:\Users\awais\.kube\config"
$kubeconfigContent = [System.IO.File]::ReadAllText($kubeconfigPath)
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($kubeconfigContent))
Write-Output $encoded
```

Copy the entire base64 output.

### 1.3 Add to GitHub Secrets

1. Go to your GitHub repository: https://github.com/awaisamjad/Real_MFA-1
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `KUBECONFIG`
5. Value: Paste the base64 encoded kubeconfig
6. Click "Add secret"

---

## Step 2: Update Kubernetes Secrets with Actual Values

The `k8s/secret.yaml` file contains placeholders. You need to update them with actual base64-encoded values.

### 2.1 Encode Your Secrets

Open PowerShell and encode your actual values:

```powershell
# Function to encode strings
function Encode-ToBase64 {
    param([string]$text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    return [Convert]::ToBase64String($bytes)
}

# Encode your secrets
Encode-ToBase64 "your-django-secret-key"  # SECRET_KEY
Encode-ToBase64 "your-db-password"  # DB_PASSWORD
Encode-ToBase64 "your-brevo-api-key"  # BREVO_API_KEY
Encode-ToBase64 "your-super-strong-redis-password"  # REDIS_PASSWORD
```

### 2.2 Update k8s/secret.yaml

Edit the file and replace the base64 values:

```yaml
data:
  SECRET_KEY: "YOUR_ENCODED_SECRET_KEY"  # Replace this
  DB_PASSWORD: "YOUR_ENCODED_DB_PASSWORD"  # Replace this
  BREVO_API_KEY: "YOUR_ENCODED_BREVO_KEY"  # Replace this
  REDIS_PASSWORD: "YOUR_ENCODED_REDIS_PASSWORD"  # Add this if missing
```

Example:
```yaml
data:
  SECRET_KEY: "<BASE64_SECRET_KEY>"
  DB_PASSWORD: "<BASE64_DB_PASSWORD>"
  BREVO_API_KEY: "<BASE64_BREVO_API_KEY>"
  REDIS_PASSWORD: "<BASE64_REDIS_PASSWORD>"
```

### 2.3 Commit and Push

```bash
git add k8s/secret.yaml
git commit -m "Use placeholder values in k8s secret template"
git push origin main
```

---

## Step 3: Update Kubernetes ConfigMap (Optional)

The `k8s/configmap.yaml` has environment variables. Update these if needed:

- `ALLOWED_HOSTS` - Your domains
- `DB_HOST` - Leave as is (internal K8s DNS)
- `REDIS_HOST` - Leave as is (internal K8s DNS)
- `EMAIL_DELIVERY_MODE` - Set to `brevo_api` (like your .env)
- `DEFAULT_FROM_EMAIL` - Your email sender
- `CSRF_TRUSTED_ORIGINS` - Your frontend domains
- `CORS_ALLOWED_ORIGINS` - Your frontend domains

If you need changes:
```bash
git add k8s/configmap.yaml
git commit -m "Update K8s ConfigMap"
git push origin main
```

---

## Step 4: Make Sure Docker Hub Credentials Are Set

Verify your GitHub repo already has these secrets from the Docker Hub setup:

- `DOCKERHUB_TOKEN` ✓ (set in previous step)

(Your Docker Hub username is hardcoded as `awaisamjad1828` in the workflow)

---

## Step 5: Verify All Workflows Are In Place

You should now have 3 GitHub Actions workflows:

1. `.github/workflows/ci.yml` - Tests code on PR
2. `.github/workflows/deploy.yml` - Builds image and pushes to Docker Hub
3. `.github/workflows/deploy-k8s.yml` - Deploys to Kubernetes

Check your repo settings:
- Actions tab → Should show all 3 workflows

---

## Step 6: Manual First Deployment (Testing)

Before auto-deploying, test manually:

### Option A: Manual GitHub Actions Trigger

1. Go to GitHub Actions tab
2. Select "Deploy to Kubernetes" workflow
3. Click "Run workflow"
4. Watch the logs

### Option B: Manual kubectl Commands

If you want to test locally first:

```bash
# First, update secrets with your actual values
# Then apply manifests manually

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres-statefulset.yaml

# Wait for DB to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s -n real-mfa-prod

kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Check status
kubectl get pods -n real-mfa-prod
kubectl get svc -n real-mfa-prod
```

---

## Step 7: Monitor Deployment

Watch the GitHub Actions log:
```
Actions → Deploy to Kubernetes → [latest run] → [job logs]
```

Or monitor locally:
```bash
# Watch pods
kubectl get pods -n real-mfa-prod -w

# Stream logs
kubectl logs -f -n real-mfa-prod -l app=real-mfa -c web

# Check events
kubectl describe pod [pod-name] -n real-mfa-prod
```

---

## Step 8: Setup Ingress & SSL

Once app is deployed, configure Ingress:

```bash
# Install Nginx Ingress (if not done by workflow)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Apply Let's Encrypt issuer (make sure to update email)
kubectl apply -f k8s/letsencrypt-issuer.yaml

# Apply Ingress
kubectl apply -f k8s/ingress.yaml

# Get LoadBalancer IP
kubectl get svc -n ingress-nginx
```

Point your DNS domains to the LoadBalancer IP.

---

## Step 9: Auto-Deployment on Git Push

Once verified, auto-deployment flows happen like this:

1. You push code to `main` branch
2. GitHub Actions `CI` workflow runs (tests + lint)
3. If CI passes, `Deploy to VPS` workflow starts
4. Docker image is built and pushed to Docker Hub
5. `Deploy to Kubernetes` workflow is triggered automatically
6. kubectl applies your K8s manifests
7. Kubernetes rolling update happens (zero downtime)
8. Your app is live with new code

---

## Monitoring & Logs

### Real-time Logs
```bash
kubectl logs -f deployment/real-mfa-web -n real-mfa-prod -c web
kubectl logs -f deployment/real-mfa-web -n real-mfa-prod -c celery-worker
```

### Past Logs
```bash
kubectl logs pod/[pod-name] -n real-mfa-prod --previous
```

### Events
```bash
kubectl get events -n real-mfa-prod
```

### Resource Usage
```bash
kubectl top nodes
kubectl top pods -n real-mfa-prod
```

### Describe Pod (for debugging)
```bash
kubectl describe pod/[pod-name] -n real-mfa-prod
```

---

## Troubleshooting

### Workflow fails at kubectl step
**Problem:** "kubeconfig: permission denied"
**Solution:** Make sure KUBECONFIG secret is properly base64 encoded with no extra spaces.

### Pods stuck in Pending
```bash
kubectl describe pod [pod-name] -n real-mfa-prod
```
Check: resources, node availability, image pull issues.

### ImagePullBackOff
```bash
kubectl describe pod [pod-name] -n real-mfa-prod
```
- Verify image exists on Docker Hub
- Check if Docker Hub login credentials are correct
- If private repo, ensure imagePullSecrets is set

### Health check failing
- Pod won't mark as 'Ready' if `/healthz/` endpoint returns non-200
- Check app is running: `kubectl exec -it [pod] -n real-mfa-prod -c web bash`
- Test endpoint: `curl http://localhost:8000/healthz/`

### Database connection error
```bash
# Check if PostgreSQL is ready
kubectl logs pod/postgres-0 -n real-mfa-prod

# Test connection
kubectl run -it --rm debug --image=postgres:16-alpine --restart=Never -- \
  psql -h postgres.real-mfa-prod.svc.cluster.local -U real_mfa_user -d real_mfa_db
```

### Out of memory errors
- Increase resource limits in `k8s/deployment.yaml`
- Check HPA is working: `kubectl get hpa -n real-mfa-prod`
- Monitor usage: `kubectl top pods -n real-mfa-prod`

---

## Next Steps

1. ✅ Add secrets to GitHub
2. ✅ Update K8s secrets with actual values  
3. ✅ Test manual deployment
4. ✅ Setup Ingress & SSL
5. Point DNS to LoadBalancer IP
6. Test auto-deployment on git push
7. Setup monitoring (Prometheus + Grafana)
8. Setup log aggregation (ELK or Loki)
9. Configure backup/restore (Velero)
10. Setup alerts and notifications

---

## Cost Optimization Tips

- Monitor resource requests (don't over-allocate)
- Use HPA to scale down when not needed
- Use DigitalOcean App Platform or managed databases if available
- Consider spot instances for non-critical workloads
- Set appropriate resource limits to prevent cost runaway

---

## Questions?

Refer to:
- [k8s/DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Advanced K8s operations
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [DigitalOcean K8s Guide](https://docs.digitalocean.com/products/kubernetes/)
