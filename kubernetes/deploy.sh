#!/bin/bash

# EKS Multi-Service Deployment Script
# This script automates the deployment of microservices to EKS cluster

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="eks-multi-service-dev"
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-YOUR_AWS_ACCOUNT_ID}"
NAMESPACE="execute-tech-academy"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}EKS Multi-Service Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Please install AWS CLI.${NC}"
    exit 1
fi

if ! command -v envsubst &> /dev/null; then
    echo -e "${YELLOW}envsubst not found. Will use manual substitution.${NC}"
    ENVSUBST_AVAILABLE=false
else
    ENVSUBST_AVAILABLE=true
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Configure kubectl
echo -e "${YELLOW}Configuring kubectl for EKS cluster...${NC}"
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to configure kubectl. Check AWS credentials and cluster name.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ kubectl configured${NC}"
echo ""

# Verify cluster connection
echo -e "${YELLOW}Verifying cluster connection...${NC}"
kubectl cluster-info &> /dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}Cannot connect to cluster. Please check your AWS credentials.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Connected to cluster${NC}"
kubectl get nodes
echo ""

# Process manifests
echo -e "${YELLOW}Processing Kubernetes manifests...${NC}"

export AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
export AWS_REGION=$AWS_REGION

cd "$(dirname "$0")/base"

# Create processed directory
mkdir -p ../processed
rm -f ../processed/*.yaml

if [ "$ENVSUBST_AVAILABLE" = true ]; then
    echo "Using envsubst for template processing..."
    for file in *.yaml; do
        envsubst < "$file" > ../processed/"$file"
        echo "  ✓ Processed $file"
    done
else
    echo "Using sed for template processing..."
    for file in *.yaml; do
        sed -e "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g" \
            -e "s/\${AWS_REGION}/$AWS_REGION/g" \
            "$file" > ../processed/"$file"
        echo "  ✓ Processed $file"
    done
fi

cd ../processed
echo -e "${GREEN}✓ Manifests processed${NC}"
echo ""

# Deploy in order
echo -e "${YELLOW}Deploying to Kubernetes...${NC}"
echo ""

# 1. Namespace
echo "1. Creating namespace..."
kubectl apply -f namespace.yaml
echo ""

# 2. ConfigMap and Secrets
echo "2. Creating ConfigMap and Secrets..."
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
echo ""

# 3. Database and Cache
echo "3. Deploying PostgreSQL and Redis..."
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml

echo "   Waiting for database and cache to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s 2>/dev/null || true
echo ""

# 4. Microservices
echo "4. Deploying microservices..."
kubectl apply -f auth-service.yaml
kubectl apply -f product-service.yaml
kubectl apply -f order-service.yaml
kubectl apply -f payment-service.yaml

echo "   Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=auth-service -n $NAMESPACE --timeout=300s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=product-service -n $NAMESPACE --timeout=300s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=order-service -n $NAMESPACE --timeout=300s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app=payment-service -n $NAMESPACE --timeout=300s 2>/dev/null || true
echo ""

# 5. API Gateway
echo "5. Deploying API Gateway..."
kubectl apply -f api-gateway.yaml

echo "   Waiting for API Gateway to be ready..."
kubectl wait --for=condition=ready pod -l app=api-gateway -n $NAMESPACE --timeout=300s 2>/dev/null || true
echo ""

# Deployment summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Show status
echo -e "${YELLOW}Current deployment status:${NC}"
kubectl get all -n $NAMESPACE
echo ""

# Get LoadBalancer URL
echo -e "${YELLOW}Getting API Gateway URL...${NC}"
echo "Note: LoadBalancer may take 2-3 minutes to become fully operational"
echo ""

for i in {1..30}; do
    GATEWAY_URL=$(kubectl get service api-gateway -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    if [ -n "$GATEWAY_URL" ]; then
        echo -e "${GREEN}API Gateway URL: http://$GATEWAY_URL:8000${NC}"
        echo ""
        echo "Test the API with:"
        echo "  curl http://$GATEWAY_URL:8000/health"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}LoadBalancer URL not yet available. Run this command later:${NC}"
        echo "  kubectl get service api-gateway -n $NAMESPACE"
    else
        sleep 2
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "1. Check pod status:"
echo "   kubectl get pods -n $NAMESPACE"
echo ""
echo "2. View logs:"
echo "   kubectl logs -f deployment/api-gateway -n $NAMESPACE"
echo ""
echo "3. Test health endpoints:"
echo "   kubectl get service api-gateway -n $NAMESPACE"
echo ""
echo "4. Monitor deployment:"
echo "   kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
echo ""
echo -e "${YELLOW}For detailed documentation, see DEPLOYMENT.md${NC}"
echo ""
