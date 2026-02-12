# EKS Multi-Service Deployment Script (PowerShell)
# This script automates the deployment of microservices to EKS cluster

$ErrorActionPreference = "Stop"

# Configuration
$CLUSTER_NAME = "eks-multi-service-dev"
$AWS_REGION = "us-east-1"
$AWS_ACCOUNT_ID = if ($env:AWS_ACCOUNT_ID) { $env:AWS_ACCOUNT_ID } else { "YOUR_AWS_ACCOUNT_ID" }
$NAMESPACE = "execute-tech-academy"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "========================================" -Color Green
Write-ColorOutput "EKS Multi-Service Deployment" -Color Green
Write-ColorOutput "========================================" -Color Green
Write-Host ""

# Check prerequisites
Write-ColorOutput "Checking prerequisites..." -Color Yellow

try {
    $null = Get-Command kubectl -ErrorAction Stop
    Write-ColorOutput "✓ kubectl found" -Color Green
} catch {
    Write-ColorOutput "kubectl not found. Please install kubectl." -Color Red
    exit 1
}

try {
    $null = Get-Command aws -ErrorAction Stop
    Write-ColorOutput "✓ AWS CLI found" -Color Green
} catch {
    Write-ColorOutput "AWS CLI not found. Please install AWS CLI." -Color Red
    exit 1
}

Write-Host ""

# Configure kubectl
Write-ColorOutput "Configuring kubectl for EKS cluster..." -Color Yellow
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "Failed to configure kubectl. Check AWS credentials and cluster name." -Color Red
    exit 1
}

Write-ColorOutput "✓ kubectl configured" -Color Green
Write-Host ""

# Verify cluster connection
Write-ColorOutput "Verifying cluster connection..." -Color Yellow
kubectl cluster-info 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "Cannot connect to cluster. Please check your AWS credentials." -Color Red
    exit 1
}

Write-ColorOutput "✓ Connected to cluster" -Color Green
kubectl get nodes
Write-Host ""

# Process manifests
Write-ColorOutput "Processing Kubernetes manifests..." -Color Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Join-Path $scriptDir "base"
$processedDir = Join-Path $scriptDir "processed"

# Create processed directory
if (Test-Path $processedDir) {
    Remove-Item -Path "$processedDir\*.yaml" -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $processedDir -Force | Out-Null
}

# Process each YAML file
Get-ChildItem -Path $baseDir -Filter "*.yaml" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace '\$\{AWS_ACCOUNT_ID\}', $AWS_ACCOUNT_ID
    $content = $content -replace '\$\{AWS_REGION\}', $AWS_REGION

    $outputFile = Join-Path $processedDir $_.Name
    Set-Content -Path $outputFile -Value $content

    Write-ColorOutput "  ✓ Processed $($_.Name)" -Color Green
}

Write-ColorOutput "✓ Manifests processed" -Color Green
Write-Host ""

# Deploy in order
Write-ColorOutput "Deploying to Kubernetes..." -Color Yellow
Write-Host ""

Set-Location $processedDir

# 1. Namespace
Write-ColorOutput "1. Creating namespace..." -Color Cyan
kubectl apply -f namespace.yaml
Write-Host ""

# 2. ConfigMap and Secrets
Write-ColorOutput "2. Creating ConfigMap and Secrets..." -Color Cyan
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
Write-Host ""

# 3. Database and Cache
Write-ColorOutput "3. Deploying PostgreSQL and Redis..." -Color Cyan
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml

Write-Host "   Waiting for database and cache to be ready..."
Start-Sleep -Seconds 30
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s 2>$null
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s 2>$null
Write-Host ""

# 4. Microservices
Write-ColorOutput "4. Deploying microservices..." -Color Cyan
kubectl apply -f auth-service.yaml
kubectl apply -f product-service.yaml
kubectl apply -f order-service.yaml
kubectl apply -f payment-service.yaml

Write-Host "   Waiting for services to be ready..."
Start-Sleep -Seconds 30
kubectl wait --for=condition=ready pod -l app=auth-service -n $NAMESPACE --timeout=300s 2>$null
kubectl wait --for=condition=ready pod -l app=product-service -n $NAMESPACE --timeout=300s 2>$null
kubectl wait --for=condition=ready pod -l app=order-service -n $NAMESPACE --timeout=300s 2>$null
kubectl wait --for=condition=ready pod -l app=payment-service -n $NAMESPACE --timeout=300s 2>$null
Write-Host ""

# 5. API Gateway
Write-ColorOutput "5. Deploying API Gateway..." -Color Cyan
kubectl apply -f api-gateway.yaml

Write-Host "   Waiting for API Gateway to be ready..."
Start-Sleep -Seconds 30
kubectl wait --for=condition=ready pod -l app=api-gateway -n $NAMESPACE --timeout=300s 2>$null
Write-Host ""

# Deployment summary
Write-ColorOutput "========================================" -Color Green
Write-ColorOutput "Deployment Complete!" -Color Green
Write-ColorOutput "========================================" -Color Green
Write-Host ""

# Show status
Write-ColorOutput "Current deployment status:" -Color Yellow
kubectl get all -n $NAMESPACE
Write-Host ""

# Get LoadBalancer URL
Write-ColorOutput "Getting API Gateway URL..." -Color Yellow
Write-Host "Note: LoadBalancer may take 2-3 minutes to become fully operational"
Write-Host ""

$maxAttempts = 30
$attempt = 0
$found = $false

while ($attempt -lt $maxAttempts) {
    $GATEWAY_URL = kubectl get service api-gateway -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>$null

    if ($GATEWAY_URL) {
        Write-ColorOutput "API Gateway URL: http://${GATEWAY_URL}:8000" -Color Green
        Write-Host ""
        Write-Host "Test the API with:"
        Write-ColorOutput "  curl http://${GATEWAY_URL}:8000/health" -Color Cyan
        $found = $true
        break
    }

    $attempt++
    Start-Sleep -Seconds 2
}

if (-not $found) {
    Write-ColorOutput "LoadBalancer URL not yet available. Run this command later:" -Color Yellow
    Write-Host "  kubectl get service api-gateway -n $NAMESPACE"
}

Write-Host ""
Write-ColorOutput "========================================" -Color Green
Write-ColorOutput "Next Steps:" -Color Green
Write-ColorOutput "========================================" -Color Green
Write-Host ""
Write-Host "1. Check pod status:"
Write-ColorOutput "   kubectl get pods -n $NAMESPACE" -Color Cyan
Write-Host ""
Write-Host "2. View logs:"
Write-ColorOutput "   kubectl logs -f deployment/api-gateway -n $NAMESPACE" -Color Cyan
Write-Host ""
Write-Host "3. Test health endpoints:"
Write-ColorOutput "   kubectl get service api-gateway -n $NAMESPACE" -Color Cyan
Write-Host ""
Write-Host "4. Monitor deployment:"
Write-ColorOutput "   kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'" -Color Cyan
Write-Host ""
Write-ColorOutput "For detailed documentation, see DEPLOYMENT.md" -Color Yellow
Write-Host ""
