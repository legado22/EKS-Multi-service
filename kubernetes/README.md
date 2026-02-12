# Kubernetes Deployment for EKS Multi-Service Application

This directory contains Kubernetes manifests and deployment scripts for deploying the microservices application to Amazon EKS.

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended)

**Automatic Deployment:**
```bash
# Push changes and deployment happens automatically
git add .
git commit -m "Deploy services"
git push origin main
```

**Manual Trigger:**
1. Go to **Actions** tab in GitHub
2. Select **Deploy to EKS** workflow
3. Click **Run workflow**
4. Choose deployment type (rolling/fresh/services)

📖 **See [GITHUB_ACTIONS_DEPLOYMENT.md](GITHUB_ACTIONS_DEPLOYMENT.md) for complete guide**

### Option 2: Automated Scripts

**For Linux/macOS:**
```bash
cd kubernetes
./deploy.sh
```

**For Windows (PowerShell):**
```powershell
cd kubernetes
.\deploy.ps1
```

### Option 3: Manual Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed step-by-step instructions.

## Directory Structure

```
kubernetes/
├── README.md                    # This file
├── DEPLOYMENT.md               # Comprehensive deployment guide
├── deploy.sh                   # Automated deployment script (Linux/macOS)
├── deploy.ps1                  # Automated deployment script (Windows)
├── base/                       # Kubernetes manifest templates
│   ├── namespace.yaml          # Namespace configuration
│   ├── configmap.yaml          # Application configuration
│   ├── secret.yaml             # Secrets (passwords, API keys)
│   ├── postgres.yaml           # PostgreSQL database
│   ├── redis.yaml              # Redis cache
│   ├── auth-service.yaml       # Authentication service
│   ├── product-service.yaml    # Product management service
│   ├── order-service.yaml      # Order processing service
│   ├── payment-service.yaml    # Payment handling service
│   └── api-gateway.yaml        # API Gateway (entry point)
└── processed/                  # Auto-generated (processed manifests)
```

## Prerequisites

Before deployment, ensure you have:

1. **AWS CLI** (v2.13.0+)
   ```bash
   aws --version
   ```

2. **kubectl** (v1.28.0+)
   ```bash
   kubectl version --client
   ```

3. **EKS Cluster**
   - Cluster Name: `eks-multi-service-dev`
   - Region: `us-east-1`
   - Status: Running

4. **Docker Images in ECR**
   All service images must be pushed to ECR:
   - `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/api-gateway:latest`
   - `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/auth-service:latest`
   - `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/product-service:latest`
   - `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/order-service:latest`
   - `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/payment-service:latest`

## Deployment Options

### Option 1: GitHub Actions (Recommended for CI/CD)

**Benefits:**
- ✅ Fully automated CI/CD pipeline
- ✅ Triggered after Docker builds complete
- ✅ Detailed deployment logs and summaries
- ✅ Built-in health checks and smoke tests
- ✅ Multiple deployment strategies (rolling, fresh, services-only)
- ✅ No local setup required

**How to use:**
1. Push changes to main branch → Automatic deployment
2. Or manually trigger from GitHub Actions UI

📖 **Complete guide:** [GITHUB_ACTIONS_DEPLOYMENT.md](GITHUB_ACTIONS_DEPLOYMENT.md)

### Option 2: Automated Scripts (Local Deployment)

The deployment scripts handle everything automatically:

**Linux/macOS:**
```bash
./deploy.sh
```

**Windows PowerShell:**
```powershell
.\deploy.ps1
```

The scripts will:
- Configure kubectl for your EKS cluster
- Process manifest templates with correct AWS account and region
- Deploy resources in the correct order
- Wait for resources to become ready
- Display the API Gateway URL when available

### Option 3: Manual Deployment (Maximum Control)

For more control over the deployment process, follow the detailed guide in [DEPLOYMENT.md](DEPLOYMENT.md).

**Quick manual deployment:**
```bash
# Configure kubectl
aws eks update-kubeconfig --name eks-multi-service-dev --region us-east-1

# Set variables
export AWS_ACCOUNT_ID=<YOUR_AWS_ACCOUNT_ID>
export AWS_REGION=us-east-1

# Process and deploy
cd base
for file in *.yaml; do
  envsubst < "$file" | kubectl apply -f -
done
```

## Configuration

### Environment Variables

The manifests use these environment variables (automatically substituted by deployment scripts):
- `AWS_ACCOUNT_ID`: `<YOUR_AWS_ACCOUNT_ID>`
- `AWS_REGION`: `us-east-1`

### Secrets Configuration

**IMPORTANT:** Before production deployment, update the secrets in [base/secret.yaml](base/secret.yaml):

```yaml
# Change these values:
SECRET_KEY: "your-secret-key-change-in-production-min-32-characters-long"
POSTGRES_PASSWORD: "change-this-in-production"
PAYSTACK_SECRET_KEY: "sk_test_your_key_here"
PAYSTACK_PUBLIC_KEY: "pk_test_your_key_here"
```

## Services Overview

| Service | Port | Replicas | Description |
|---------|------|----------|-------------|
| **API Gateway** | 8000 | 3 | Entry point (LoadBalancer) |
| **Auth Service** | 8001 | 2 | User authentication |
| **Product Service** | 8002 | 2 | Product catalog management |
| **Order Service** | 8003 | 2 | Order processing |
| **Payment Service** | 8004 | 2 | Payment handling |
| **PostgreSQL** | 5432 | 1 | Database |
| **Redis** | 6379 | 1 | Cache |

## Accessing the Application

After deployment, get the API Gateway URL:

```bash
kubectl get service api-gateway -n execute-tech-academy
```

The LoadBalancer URL will be available within 2-3 minutes. Access your application at:
```
http://<loadbalancer-url>:8000
```

## Common Commands

### Check deployment status:
```bash
kubectl get all -n execute-tech-academy
```

### View pod logs:
```bash
kubectl logs -f deployment/api-gateway -n execute-tech-academy
```

### Check pod health:
```bash
kubectl get pods -n execute-tech-academy
```

### Scale a service:
```bash
kubectl scale deployment/product-service --replicas=5 -n execute-tech-academy
```

### Update service image:
```bash
kubectl set image deployment/auth-service \
  auth-service=<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/auth-service:v1.1.0 \
  -n execute-tech-academy
```

### Delete all resources:
```bash
kubectl delete namespace execute-tech-academy
```

## Troubleshooting

### Pods not starting?
```bash
kubectl describe pod <pod-name> -n execute-tech-academy
kubectl logs <pod-name> -n execute-tech-academy
```

### ImagePullBackOff error?
Verify ECR images exist and node role has pull permissions:
```bash
aws ecr list-images --repository-name eks-multi-service/auth-service
```

### Service not reachable?
Check endpoints and service connectivity:
```bash
kubectl get endpoints -n execute-tech-academy
kubectl get service -n execute-tech-academy
```

For detailed troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Load Balancer                        │
│                    (api-gateway:8000)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │      API Gateway Pods        │
          │         (3 replicas)         │
          └──────────────┬───────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│   Auth   │      │ Product  │      │  Order   │
│ Service  │      │ Service  │      │ Service  │
│ (8001)   │      │ (8002)   │      │ (8003)   │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │
     └─────────────────┼──────────────────┘
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
     ┌──────────┐           ┌──────────┐
     │PostgreSQL│           │  Redis   │
     │  (5432)  │           │  (6379)  │
     └──────────┘           └──────────┘
```

## Production Considerations

Before going to production:

- [ ] Update all secrets and passwords
- [ ] Configure TLS/SSL certificates
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure autoscaling (HPA)
- [ ] Implement database backups
- [ ] Set up centralized logging
- [ ] Configure Network Policies
- [ ] Review resource limits
- [ ] Implement CI/CD pipeline

## Documentation

- **[GITHUB_ACTIONS_DEPLOYMENT.md](GITHUB_ACTIONS_DEPLOYMENT.md)** - GitHub Actions CI/CD deployment guide (Recommended)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Manual deployment guide with step-by-step instructions
- **[README.md](README.md)** - This file (Quick start and overview)
- **[../README.md](../README.md)** - Project overview and infrastructure documentation
- **[../terraform/](../terraform/)** - Infrastructure as Code (Terraform)

## Support

For issues or questions:
1. Check the [Troubleshooting](DEPLOYMENT.md#troubleshooting) section in DEPLOYMENT.md
2. Review pod logs: `kubectl logs <pod-name> -n execute-tech-academy`
3. Check events: `kubectl get events -n execute-tech-academy --sort-by='.lastTimestamp'`

---

**Last Updated**: 2026-01-26
**Cluster**: eks-multi-service-dev
**Region**: us-east-1
**Account**: <YOUR_AWS_ACCOUNT_ID>
