# Kubernetes Deployment - Quick Start

## 🎯 TL;DR - Deploy Now

### Automatic Deployment (Easiest)
```bash
git push origin main
```
That's it! Deployment happens automatically via GitHub Actions.

### Manual Trigger from GitHub
1. Go to: **GitHub → Actions → Deploy to EKS**
2. Click: **Run workflow**
3. Select: `rolling` (recommended)
4. Click: **Run workflow**
5. Wait 3-5 minutes
6. Get URL from workflow output

## 📋 Deployment Methods Comparison

| Method | When to Use | Time | Downtime |
|--------|-------------|------|----------|
| **GitHub Actions (Rolling)** | Production updates | 3-5 min | None |
| **GitHub Actions (Services)** | Quick service updates | 2-3 min | None |
| **GitHub Actions (Fresh)** | Major changes, testing | 5-8 min | 2-5 min |
| **Local Script** | Local development | 5-10 min | Varies |
| **Manual kubectl** | Debugging, learning | 10-20 min | Varies |

## 🔄 Common Workflows

### Deploy New Feature
```bash
# 1. Make changes
vim services/auth-service/main.py

# 2. Commit and push
git add .
git commit -m "Add new feature"
git push origin main

# 3. Watch deployment
# Go to: GitHub → Actions → Watch the build and deploy
```

### Quick Service Update
```bash
# 1. Update service code
vim services/product-service/app.py

# 2. Push changes
git add services/product-service/
git commit -m "Update product service"
git push origin main

# 3. Builds and deploys automatically
```

### Update Kubernetes Config
```bash
# 1. Update manifests
vim kubernetes/base/auth-service.yaml

# 2. Push changes
git add kubernetes/
git commit -m "Update resource limits"
git push origin main

# 3. Deploys new configuration
```

## 🚨 Emergency Procedures

### Rollback Deployment
```bash
# Option 1: Via kubectl
aws eks update-kubeconfig --name eks-multi-service-dev --region us-east-1
kubectl rollout undo deployment/auth-service -n execute-tech-academy

# Option 2: Via GitHub Actions
# Go to Actions → Deploy to EKS → Run workflow with rolling deployment
```

### Check Deployment Status
```bash
# Configure kubectl
aws eks update-kubeconfig --name eks-multi-service-dev --region us-east-1

# Check pods
kubectl get pods -n execute-tech-academy

# Check services
kubectl get services -n execute-tech-academy

# View logs
kubectl logs -f deployment/api-gateway -n execute-tech-academy
```

### Get Application URL
```bash
# Get LoadBalancer URL
kubectl get service api-gateway -n execute-tech-academy

# Or from GitHub Actions output
# Go to: Actions → Latest Deploy to EKS run → Check Summary
```

## 🎯 Deployment Strategies

### Rolling Deployment (Default) ✅
**Use for:** Production updates, normal deployments
```
Behavior: Zero downtime, gradual pod replacement
Command: Push to main or select "rolling" in workflow
```

### Services Only ⚡
**Use for:** Quick service updates without infrastructure changes
```
Behavior: Only updates service deployments
Command: Select "services" in workflow
```

### Fresh Deployment 🆕
**Use for:** Major changes, stuck resources, clean slate
```
Behavior: Deletes everything and recreates
Command: Select "fresh" in workflow
⚠️ Warning: Downtime expected, data will be lost
```

## 📊 Monitoring

### View Deployment Progress
```
GitHub → Actions → Deploy to EKS → Click on running workflow
```

### Check Application Health
```bash
# Get URL
GATEWAY_URL=$(kubectl get service api-gateway -n execute-tech-academy -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health
curl http://$GATEWAY_URL:8000/health
```

### View Pod Status
```bash
kubectl get pods -n execute-tech-academy -w
```

## 🔧 Troubleshooting

### Pods Not Starting
```bash
# Check pod status
kubectl get pods -n execute-tech-academy

# Describe problematic pod
kubectl describe pod <pod-name> -n execute-tech-academy

# View logs
kubectl logs <pod-name> -n execute-tech-academy
```

### ImagePullBackOff Error
```bash
# Verify images exist
aws ecr list-images --repository-name eks-multi-service/auth-service

# Check if Docker build completed successfully
# Go to: GitHub → Actions → Build and Push to ECR
```

### LoadBalancer Not Getting URL
```bash
# Wait 2-3 minutes, then check again
kubectl get service api-gateway -n execute-tech-academy

# Check service events
kubectl describe service api-gateway -n execute-tech-academy
```

## 📚 Full Documentation

- **[GITHUB_ACTIONS_DEPLOYMENT.md](GITHUB_ACTIONS_DEPLOYMENT.md)** - Complete GitHub Actions guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed manual deployment guide
- **[README.md](README.md)** - Full documentation

## 🆘 Getting Help

1. Check workflow output in GitHub Actions
2. View pod logs: `kubectl logs <pod-name> -n execute-tech-academy`
3. Check events: `kubectl get events -n execute-tech-academy --sort-by='.lastTimestamp'`
4. See troubleshooting sections in documentation

## ⚙️ Configuration Files

```
.github/workflows/
├── deploy-to-eks.yml          # Main deployment workflow
└── docker-build.yml           # Docker image build workflow

kubernetes/base/
├── namespace.yaml             # Namespace
├── configmap.yaml            # Configuration
├── secret.yaml               # Secrets (update before production!)
├── postgres.yaml             # Database
├── redis.yaml                # Cache
├── auth-service.yaml         # Auth service
├── product-service.yaml      # Product service
├── order-service.yaml        # Order service
├── payment-service.yaml      # Payment service
└── api-gateway.yaml          # API Gateway
```

## 🔐 Security Notes

Before production:
- [ ] Update secrets in `kubernetes/base/secret.yaml`
- [ ] Change `POSTGRES_PASSWORD`
- [ ] Change `SECRET_KEY` (min 32 characters)
- [ ] Add real Paystack API keys
- [ ] Configure TLS/SSL for LoadBalancer
- [ ] Review IAM permissions

## 🎉 Success Criteria

Your deployment is successful when:
- ✅ All pods are in `Running` state
- ✅ LoadBalancer has an external URL
- ✅ Health endpoint returns 200: `curl http://<url>:8000/health`
- ✅ All services are accessible
- ✅ Smoke tests pass in GitHub Actions

---

**Cluster:** eks-multi-service-dev
**Region:** us-east-1
**Namespace:** execute-tech-academy
**Account:** <YOUR_AWS_ACCOUNT_ID>
