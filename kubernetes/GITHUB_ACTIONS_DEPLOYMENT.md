# GitHub Actions Deployment Guide

This guide explains how to use GitHub Actions to automatically deploy your microservices to Amazon EKS.

## Overview

The deployment workflow ([deploy-to-eks.yml](../.github/workflows/deploy-to-eks.yml)) provides automated deployment to your EKS cluster with multiple trigger options and deployment strategies.

## Workflow Features

✅ **Automatic Deployment** - Triggers after Docker images are built
✅ **Manual Deployment** - Deploy on-demand with custom options
✅ **Multiple Strategies** - Rolling, fresh, or services-only deployment
✅ **Health Checks** - Automatic verification of deployed services
✅ **Smoke Tests** - Post-deployment testing
✅ **Detailed Reporting** - Comprehensive deployment summaries

## Trigger Methods

### 1. Automatic Deployment (Recommended)

The workflow automatically deploys after Docker images are successfully built and pushed to ECR:

```bash
# Make changes to your services
git add services/auth-service/
git commit -m "Update auth service"
git push origin main
```

**Flow:**
1. Pushes trigger `docker-build.yml` workflow
2. Docker images are built and pushed to ECR
3. `deploy-to-eks.yml` automatically triggers
4. Services are deployed to EKS cluster

### 2. Manual Deployment

Deploy manually from GitHub Actions interface:

**Steps:**
1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **Deploy to EKS** workflow
4. Click **Run workflow**
5. Configure options:
   - **Environment**: `dev` (default)
   - **Deployment type**:
     - `rolling` - Update existing deployments (default, zero downtime)
     - `fresh` - Delete and recreate all resources
     - `services` - Only update service deployments
6. Click **Run workflow**

### 3. Manifest Changes

Automatically deploys when Kubernetes manifests are updated:

```bash
# Update Kubernetes manifests
git add kubernetes/
git commit -m "Update resource limits"
git push origin main
```

## Deployment Strategies

### Rolling Deployment (Default)

**When to use:** Regular updates, production deployments

**Behavior:**
- Updates existing deployments
- Zero downtime
- Gradual pod replacement
- Automatic rollback on failure

```yaml
# Triggered automatically or via workflow_dispatch with:
deploy_type: rolling
```

**What happens:**
1. Applies all manifests
2. Kubernetes updates deployments with new images
3. Old pods are gradually replaced
4. Health checks verify new pods
5. Old pods are terminated

### Fresh Deployment

**When to use:** Major changes, testing, fixing stuck resources

**Behavior:**
- Deletes entire namespace
- Recreates all resources from scratch
- Downtime expected (2-5 minutes)
- Clean state

```yaml
# Via workflow_dispatch with:
deploy_type: fresh
```

**What happens:**
1. Deletes namespace `execute-tech-academy`
2. Waits for cleanup
3. Creates namespace
4. Deploys infrastructure (PostgreSQL, Redis)
5. Deploys microservices
6. Deploys API Gateway

**⚠️ Warning:** Fresh deployment will delete all data in PostgreSQL. Backup first!

### Services Only

**When to use:** Quick service updates without touching infrastructure

**Behavior:**
- Only updates service deployments
- Skips ConfigMap, Secret, PostgreSQL, Redis
- Fastest deployment option

```yaml
# Via workflow_dispatch with:
deploy_type: services
```

**What happens:**
1. Updates auth-service
2. Updates product-service
3. Updates order-service
4. Updates payment-service
5. Updates api-gateway

## Workflow Steps Explained

### 1. Authentication
```yaml
- Configure AWS Credentials (OIDC)
```
Uses OpenID Connect to securely authenticate with AWS without storing credentials.

### 2. Cluster Configuration
```yaml
- Configure kubectl
- Check Cluster Nodes
```
Sets up kubectl to communicate with your EKS cluster and verifies cluster health.

### 3. Manifest Processing
```yaml
- Process Kubernetes Manifests
```
Replaces template variables:
- `${AWS_ACCOUNT_ID}` → `<YOUR_AWS_ACCOUNT_ID>`
- `${AWS_REGION}` → `us-east-1`

### 4. Deployment
```yaml
- Deploy Infrastructure / Services / Rolling
```
Applies manifests based on selected deployment strategy.

### 5. Verification
```yaml
- Wait for Deployments to be Ready
- Verify Deployment
```
Waits for pods to be ready and checks deployment status.

### 6. Health Checks
```yaml
- Get API Gateway URL
- Test Health Endpoints
```
Retrieves LoadBalancer URL and tests service health.

### 7. Smoke Tests
```yaml
- Run Basic Smoke Tests
```
Performs basic API tests to verify deployment success.

## Monitoring Deployments

### View Workflow Runs

1. Go to **Actions** tab in GitHub
2. Click on **Deploy to EKS** workflow
3. View recent runs and their status

### Workflow Output

Each deployment provides detailed information:

**Job Summary includes:**
- AWS identity verification
- Cluster information
- Node status
- Processed manifests
- Deployment status
- Pod status
- LoadBalancer URL
- Health check results
- Rollout status
- Resource counts

**Example Summary:**
```
🔐 AWS Identity
✓ Authenticated as: arn:aws:sts::<YOUR_AWS_ACCOUNT_ID>:assumed-role/...

⚙️ Configuring kubectl for EKS
Cluster: eks-multi-service-dev
Region: us-east-1
Namespace: execute-tech-academy

📝 Processing Kubernetes Manifests
✓ Processed namespace.yaml
✓ Processed configmap.yaml
...

📊 Deployment Status
All pods: 11/11 running

🌐 API Gateway Information
LoadBalancer URL: http://abc123.us-east-1.elb.amazonaws.com:8000
Health Check: http://abc123.us-east-1.elb.amazonaws.com:8000/health

✅ All pods are running successfully!
```

## Troubleshooting Deployments

### Deployment Failed

If deployment fails:

1. **Check Workflow Logs**
   - Go to failed workflow run
   - Expand failed step
   - Read error messages

2. **Common Issues:**

   **Image Pull Error:**
   ```
   Error: ImagePullBackOff
   ```
   - Verify images exist in ECR
   - Check ECR repository policy
   - Ensure node role has pull permissions

   **Resource Issues:**
   ```
   Error: Insufficient cpu/memory
   ```
   - Scale up node group
   - Reduce resource requests
   - Add more nodes

   **Configuration Error:**
   ```
   Error: CrashLoopBackOff
   ```
   - Check pod logs in workflow output
   - Verify environment variables
   - Check database connectivity

3. **Manual Investigation**

   After failed deployment, investigate manually:
   ```bash
   # Configure kubectl
   aws eks update-kubeconfig --name eks-multi-service-dev --region us-east-1

   # Check pods
   kubectl get pods -n execute-tech-academy

   # View logs
   kubectl logs <pod-name> -n execute-tech-academy

   # Describe pod
   kubectl describe pod <pod-name> -n execute-tech-academy

   # Check events
   kubectl get events -n execute-tech-academy --sort-by='.lastTimestamp'
   ```

### Rollback Failed Deployment

**Option 1: Via Workflow**
1. Go to **Actions** → **Deploy to EKS**
2. Click **Run workflow**
3. Select `rolling` deployment
4. Previous working images will be deployed

**Option 2: Manual Rollback**
```bash
# Rollback specific deployment
kubectl rollout undo deployment/auth-service -n execute-tech-academy

# Rollback to specific revision
kubectl rollout history deployment/auth-service -n execute-tech-academy
kubectl rollout undo deployment/auth-service --to-revision=2 -n execute-tech-academy
```

**Option 3: Fresh Deployment**
1. Go to **Actions** → **Deploy to EKS**
2. Click **Run workflow**
3. Select `fresh` deployment type
4. This recreates everything from scratch

## Environment Variables

The workflow uses these environment variables:

```yaml
AWS_REGION: us-east-1
CLUSTER_NAME: eks-multi-service-dev
NAMESPACE: execute-tech-academy
AWS_ACCOUNT_ID: '<YOUR_AWS_ACCOUNT_ID>'
```

To deploy to different environments, modify these in the workflow file.

## Secrets Required

The workflow requires this GitHub secret:

- **`AWS_ROLE_ARN`**: ARN of the GitHub Actions IAM role
  - Example: `arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:role/eks-multi-service-dev-github-actions-role`
  - Already configured in your repository

## Advanced Usage

### Deploy Specific Service

To deploy only a specific service:

1. Update the service manifest in `kubernetes/base/`
2. Commit and push
3. Run workflow with `services` deployment type

### Custom Deployment Script

For complex scenarios, create a custom deployment:

```bash
# In your repository
git add .github/workflows/custom-deploy.yml
git commit -m "Add custom deployment"
git push
```

### Multiple Environments

To support multiple environments (dev, staging, prod):

1. Create separate manifest directories:
   ```
   kubernetes/
   ├── dev/
   ├── staging/
   └── prod/
   ```

2. Update workflow to use environment-specific paths:
   ```yaml
   - name: Select Environment
     run: |
       if [ "${{ github.event.inputs.environment }}" == "prod" ]; then
         export MANIFEST_DIR="kubernetes/prod"
       else
         export MANIFEST_DIR="kubernetes/dev"
       fi
   ```

## Best Practices

### 1. Use Rolling Deployments for Production
- Zero downtime
- Automatic rollback
- Gradual updates

### 2. Test in Dev First
- Deploy to dev environment
- Run smoke tests
- Verify functionality
- Then deploy to production

### 3. Monitor Deployments
- Watch workflow output
- Check pod status
- Verify health endpoints
- Monitor application logs

### 4. Backup Before Fresh Deployments
```bash
# Backup PostgreSQL data before fresh deployment
kubectl exec -n execute-tech-academy deployment/postgres -- \
  pg_dumpall -U admin > backup.sql
```

### 5. Use Semantic Versioning
```bash
# Tag releases
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Update image tags in manifests
image: <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/auth-service:v1.0.0
```

## Integration with Docker Build Workflow

The workflows are integrated:

```
Push to main
    ↓
Docker Build Workflow
    ↓ (on success)
Deploy to EKS Workflow
    ↓
Smoke Tests
    ↓
Production Ready
```

This ensures:
- Only tested images are deployed
- Automatic deployment after builds
- Continuous delivery pipeline

## Next Steps

After successful deployment:

1. **Monitor Application**
   - Check CloudWatch logs
   - Set up alerts
   - Monitor resource usage

2. **Set Up Production**
   - Update secrets
   - Configure TLS
   - Set up custom domain
   - Enable autoscaling

3. **Implement CI/CD Enhancements**
   - Add integration tests
   - Implement canary deployments
   - Add approval gates
   - Set up notifications

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [kubectl Documentation](https://kubernetes.io/docs/reference/kubectl/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [DEPLOYMENT.md](DEPLOYMENT.md) - Manual deployment guide

---

**Last Updated**: 2026-01-26
**Workflow**: deploy-to-eks.yml
**Cluster**: eks-multi-service-dev
