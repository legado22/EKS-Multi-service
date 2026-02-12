# EKS Multi-Service Application Deployment Guide

This guide provides step-by-step instructions to deploy the microservices application to your Amazon EKS cluster using container images from Amazon ECR.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Detailed Deployment Steps](#detailed-deployment-steps)
- [Verification](#verification)
- [Accessing the Application](#accessing-the-application)
- [Updating Deployments](#updating-deployments)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
```bash
# AWS CLI (version 2.13.0 or later)
aws --version

# kubectl (version 1.28.0 or later)
kubectl version --client

# Optional: envsubst (for template substitution)
envsubst --version
```

### AWS Configuration
- AWS CLI configured with appropriate credentials
- AWS Account ID: `<YOUR_AWS_ACCOUNT_ID>`
- Region: `us-east-1`
- EKS Cluster: `eks-multi-service-dev`

### Docker Images in ECR
Ensure all service images are built and pushed to ECR:
- `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/api-gateway:latest`
- `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/auth-service:latest`
- `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/product-service:latest`
- `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/order-service:latest`
- `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/payment-service:latest`

## Architecture Overview

The application consists of:
- **API Gateway**: Entry point (LoadBalancer) - Port 8000
- **Auth Service**: User authentication - Port 8001
- **Product Service**: Product catalog management - Port 8002
- **Order Service**: Order processing - Port 8003
- **Payment Service**: Payment handling - Port 8004
- **PostgreSQL**: Database for persistent storage
- **Redis**: Caching and session management

## Quick Start

```bash
# 1. Configure kubectl for your EKS cluster
aws eks update-kubeconfig --name eks-multi-service-dev --region us-east-1

# 2. Set environment variables
export AWS_ACCOUNT_ID=<YOUR_AWS_ACCOUNT_ID>
export AWS_REGION=us-east-1

# 3. Navigate to kubernetes directory
cd kubernetes/base

# 4. Update image references and deploy
for file in *.yaml; do
  envsubst < "$file" | kubectl apply -f -
done

# 5. Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n execute-tech-academy --timeout=300s

# 6. Get the API Gateway URL
kubectl get service api-gateway -n execute-tech-academy
```

## Detailed Deployment Steps

### Step 1: Configure kubectl Access to EKS Cluster

```bash
# Update kubeconfig to access your EKS cluster
aws eks update-kubeconfig --name eks-multi-service-dev --region us-east-1

# Verify connection
kubectl cluster-info
kubectl get nodes
```

Expected output:
```
NAME                            STATUS   ROLES    AGE   VERSION
ip-10-0-xx-xx.ec2.internal     Ready    <none>   5m    v1.29.x
ip-10-0-xx-xx.ec2.internal     Ready    <none>   5m    v1.29.x
ip-10-0-xx-xx.ec2.internal     Ready    <none>   5m    v1.29.x
```

### Step 2: Prepare Kubernetes Manifests

Navigate to the kubernetes directory:
```bash
cd kubernetes/base
```

Your manifests contain placeholder variables that need to be replaced:
- `${AWS_ACCOUNT_ID}` → `<YOUR_AWS_ACCOUNT_ID>`
- `${AWS_REGION}` → `us-east-1`

**Option A: Using envsubst (Recommended)**
```bash
export AWS_ACCOUNT_ID=<YOUR_AWS_ACCOUNT_ID>
export AWS_REGION=us-east-1

# Create a temporary directory for processed manifests
mkdir -p ../processed

# Process all YAML files
for file in *.yaml; do
  envsubst < "$file" > ../processed/"$file"
done

cd ../processed
```

**Option B: Manual replacement (if envsubst not available)**
```bash
# For PowerShell on Windows:
cd kubernetes/base
Get-ChildItem *.yaml | ForEach-Object {
  (Get-Content $_) -replace '\$\{AWS_ACCOUNT_ID\}', '<YOUR_AWS_ACCOUNT_ID>' -replace '\$\{AWS_REGION\}', 'us-east-1' | Set-Content "../processed/$($_.Name)"
}
cd ../processed
```

### Step 3: Customize Secrets (Important!)

Before deploying, update the secrets in `secret.yaml`:

```bash
# Edit the secret file
kubectl create secret generic app-secrets \
  --namespace=execute-tech-academy \
  --from-literal=SECRET_KEY="your-production-secret-key-min-32-chars" \
  --from-literal=POSTGRES_PASSWORD="your-secure-postgres-password" \
  --from-literal=DATABASE_URL_AUTH="postgresql://admin:your-password@postgres-service:5432/auth_db" \
  --from-literal=DATABASE_URL_PRODUCT="postgresql://admin:your-password@postgres-service:5432/product_db" \
  --from-literal=DATABASE_URL_ORDER="postgresql://admin:your-password@postgres-service:5432/order_db" \
  --from-literal=DATABASE_URL_PAYMENT="postgresql://admin:your-password@postgres-service:5432/payment_db" \
  --from-literal=PAYSTACK_SECRET_KEY="your-paystack-secret-key" \
  --from-literal=PAYSTACK_PUBLIC_KEY="your-paystack-public-key" \
  --dry-run=client -o yaml > secret-custom.yaml

# Review and apply
kubectl apply -f secret-custom.yaml
```

### Step 4: Deploy Infrastructure Components

Deploy in the following order to ensure dependencies are met:

**4.1 Create Namespace**
```bash
kubectl apply -f namespace.yaml
```

**4.2 Create ConfigMap and Secrets**
```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml  # or secret-custom.yaml if you customized
```

**4.3 Deploy Database and Cache**
```bash
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
```

Wait for database and cache to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=postgres -n execute-tech-academy --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n execute-tech-academy --timeout=300s
```

**4.4 Deploy Microservices**
```bash
kubectl apply -f auth-service.yaml
kubectl apply -f product-service.yaml
kubectl apply -f order-service.yaml
kubectl apply -f payment-service.yaml
```

Wait for services to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=auth-service -n execute-tech-academy --timeout=300s
kubectl wait --for=condition=ready pod -l app=product-service -n execute-tech-academy --timeout=300s
kubectl wait --for=condition=ready pod -l app=order-service -n execute-tech-academy --timeout=300s
kubectl wait --for=condition=ready pod -l app=payment-service -n execute-tech-academy --timeout=300s
```

**4.5 Deploy API Gateway**
```bash
kubectl apply -f api-gateway.yaml
```

Wait for API Gateway to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=api-gateway -n execute-tech-academy --timeout=300s
```

### Step 5: Deploy Everything at Once (Alternative)

If you prefer to deploy all resources at once:

```bash
# From kubernetes/processed directory
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f auth-service.yaml
kubectl apply -f product-service.yaml
kubectl apply -f order-service.yaml
kubectl apply -f payment-service.yaml
kubectl apply -f api-gateway.yaml

# Or use a single command (less control)
kubectl apply -f .
```

## Verification

### Check Deployment Status

```bash
# View all resources in the namespace
kubectl get all -n execute-tech-academy

# Check pod status
kubectl get pods -n execute-tech-academy

# Check service endpoints
kubectl get services -n execute-tech-academy

# View pod logs for a specific service
kubectl logs -f deployment/auth-service -n execute-tech-academy

# Describe a pod to see events
kubectl describe pod <pod-name> -n execute-tech-academy
```

Expected output for `kubectl get pods`:
```
NAME                               READY   STATUS    RESTARTS   AGE
api-gateway-xxxxxxxxxx-xxxxx       1/1     Running   0          5m
auth-service-xxxxxxxxxx-xxxxx      1/1     Running   0          5m
auth-service-xxxxxxxxxx-xxxxx      1/1     Running   0          5m
order-service-xxxxxxxxxx-xxxxx     1/1     Running   0          5m
order-service-xxxxxxxxxx-xxxxx     1/1     Running   0          5m
payment-service-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
payment-service-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
postgres-xxxxxxxxxx-xxxxx          1/1     Running   0          10m
product-service-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
product-service-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
redis-xxxxxxxxxx-xxxxx             1/1     Running   0          10m
```

### Health Check Endpoints

Once the API Gateway LoadBalancer is provisioned, test the health endpoints:

```bash
# Get the LoadBalancer URL
GATEWAY_URL=$(kubectl get service api-gateway -n execute-tech-academy -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test API Gateway health
curl http://$GATEWAY_URL:8000/health

# Test individual service health (from within the cluster)
kubectl exec -n execute-tech-academy deployment/api-gateway -- curl http://auth-service:8001/health
kubectl exec -n execute-tech-academy deployment/api-gateway -- curl http://product-service:8002/health
kubectl exec -n execute-tech-academy deployment/api-gateway -- curl http://order-service:8003/health
kubectl exec -n execute-tech-academy deployment/api-gateway -- curl http://payment-service:8004/health
```

## Accessing the Application

### Get API Gateway URL

The API Gateway is exposed via an AWS LoadBalancer:

```bash
# Get the LoadBalancer DNS name
kubectl get service api-gateway -n execute-tech-academy

# Or extract just the hostname
kubectl get service api-gateway -n execute-tech-academy -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Output example:
```
NAME          TYPE           CLUSTER-IP      EXTERNAL-IP                                                              PORT(S)          AGE
api-gateway   LoadBalancer   10.100.xx.xx    a1234567890abcdef.us-east-1.elb.amazonaws.com                          8000:31234/TCP   5m
```

### Access the Application

```bash
# Set the gateway URL
export GATEWAY_URL=a1234567890abcdef.us-east-1.elb.amazonaws.com

# Test the API
curl http://$GATEWAY_URL:8000/health

# Example API calls
curl http://$GATEWAY_URL:8000/api/products
curl http://$GATEWAY_URL:8000/api/auth/status
```

Note: It may take 2-3 minutes for the LoadBalancer to become fully operational after creation.

## Updating Deployments

### Update Application Images

When you push new images to ECR:

```bash
# Tag your new image
docker tag your-service:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/your-service:v1.2.0

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/your-service:v1.2.0

# Update the deployment
kubectl set image deployment/your-service your-service=<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/eks-multi-service/your-service:v1.2.0 -n execute-tech-academy

# Or edit the manifest and reapply
kubectl apply -f your-service.yaml

# Watch the rollout
kubectl rollout status deployment/your-service -n execute-tech-academy
```

### Rollback a Deployment

```bash
# View rollout history
kubectl rollout history deployment/your-service -n execute-tech-academy

# Rollback to previous version
kubectl rollout undo deployment/your-service -n execute-tech-academy

# Rollback to specific revision
kubectl rollout undo deployment/your-service --to-revision=2 -n execute-tech-academy
```

### Scale Deployments

```bash
# Scale a specific service
kubectl scale deployment/product-service --replicas=5 -n execute-tech-academy

# Check the new pod count
kubectl get deployment product-service -n execute-tech-academy
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n execute-tech-academy

# Describe pod to see events
kubectl describe pod <pod-name> -n execute-tech-academy

# Check pod logs
kubectl logs <pod-name> -n execute-tech-academy

# Check previous container logs (if pod restarted)
kubectl logs <pod-name> -n execute-tech-academy --previous
```

Common issues:
- **ImagePullBackOff**: ECR authentication issue or image doesn't exist
- **CrashLoopBackOff**: Application error, check logs
- **Pending**: Insufficient resources or node issues

### ImagePullBackOff Error

If you see `ImagePullBackOff`, the EKS nodes cannot pull images from ECR:

```bash
# Check the exact error
kubectl describe pod <pod-name> -n execute-tech-academy

# Verify ECR repository policy allows EKS node role
aws ecr get-repository-policy --repository-name eks-multi-service/auth-service

# Verify images exist in ECR
aws ecr list-images --repository-name eks-multi-service/auth-service
```

### Service Not Reachable

```bash
# Check if service exists
kubectl get service -n execute-tech-academy

# Check service endpoints
kubectl get endpoints -n execute-tech-academy

# Test service from within cluster
kubectl run test-pod --image=busybox -n execute-tech-academy --rm -it -- wget -O- http://auth-service:8001/health
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl logs -f deployment/postgres -n execute-tech-academy

# Test database connectivity from a service pod
kubectl exec -it deployment/auth-service -n execute-tech-academy -- sh
# Inside the pod:
nc -zv postgres-service 5432
```

### View All Events

```bash
# See all events in the namespace
kubectl get events -n execute-tech-academy --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n execute-tech-academy --watch
```

### Resource Issues

```bash
# Check node resources
kubectl top nodes

# Check pod resource usage
kubectl top pods -n execute-tech-academy

# Describe nodes to see resource allocation
kubectl describe nodes
```

### Clean Up and Redeploy

```bash
# Delete all resources in namespace (except the namespace itself)
kubectl delete all --all -n execute-tech-academy

# Or delete everything including namespace
kubectl delete namespace execute-tech-academy

# Redeploy from scratch
kubectl apply -f namespace.yaml
# ... continue with deployment steps
```

## Production Recommendations

Before going to production:

1. **Update Secrets**: Change all default passwords and API keys in `secret.yaml`
2. **Configure TLS**: Set up TLS certificates for the LoadBalancer (use AWS Certificate Manager)
3. **Set up Monitoring**: Deploy Prometheus/Grafana or use AWS CloudWatch Container Insights
4. **Configure Autoscaling**: Set up Horizontal Pod Autoscaler (HPA) for services
5. **Backup Database**: Configure PostgreSQL backups using snapshots or pg_dump
6. **Update Resource Limits**: Adjust CPU/memory based on actual usage patterns
7. **Set up Logging**: Configure centralized logging (CloudWatch Logs, ELK stack, etc.)
8. **Security Hardening**: Implement Network Policies, Pod Security Standards, and RBAC

## Additional Resources

- [Amazon EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

---

**Last Updated**: 2026-01-26
**Cluster**: eks-multi-service-dev
**Region**: us-east-1
**Account**: <YOUR_AWS_ACCOUNT_ID>
