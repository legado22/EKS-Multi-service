# EKS Multi-Service VPC Deployment Setup Script (PowerShell)
# This configures single NAT Gateway for cost-optimized dev environment

Write-Host "======================================" -ForegroundColor Green
Write-Host "EKS Multi-Service Deployment Setup" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Find repository root
$RepoRoot = git rev-parse --show-toplevel 2>$null

if (-not $RepoRoot) {
    Write-Host "Error: Not in a Git repository!" -ForegroundColor Red
    exit 1
}

Write-Host "Repository root: $RepoRoot" -ForegroundColor Green
Set-Location $RepoRoot

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Step 1: Update VPC Module Variables" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Update VPC module variables.tf
$vpcVariables = @'
variable "project_name" {
  description = "Project name to be used as a prefix"
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name for subnet tagging"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets"
  type        = list(string)
}

variable "private_db_subnet_cidrs" {
  description = "CIDR blocks for private database subnets"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all private subnets (cost optimization)"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}
'@

$vpcVariables | Out-File -FilePath "eks-multi-service/terraform/modules/vpc/variables.tf" -Encoding UTF8 -NoNewline

Write-Host "✓ VPC module variables updated" -ForegroundColor Green

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Step 2: Update Dev Environment Variables" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$devVariables = @'
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "eks-multi-service"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "CIDR blocks for private application subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
}

variable "private_db_subnet_cidrs" {
  description = "CIDR blocks for private database subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all private subnets"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = false
}
'@

$devVariables | Out-File -FilePath "eks-multi-service/terraform/environments/dev/variables.tf" -Encoding UTF8 -NoNewline

Write-Host "✓ Dev environment variables updated" -ForegroundColor Green

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Step 3: Update Dev Main.tf" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$devMain = @'
module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  cluster_name = "${var.project_name}-${var.environment}"
  vpc_cidr     = var.vpc_cidr

  availability_zones       = var.availability_zones
  public_subnet_cidrs      = var.public_subnet_cidrs
  private_app_subnet_cidrs = var.private_app_subnet_cidrs
  private_db_subnet_cidrs  = var.private_db_subnet_cidrs

  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway
  enable_flow_logs   = var.enable_flow_logs

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
'@

$devMain | Out-File -FilePath "eks-multi-service/terraform/environments/dev/main.tf" -Encoding UTF8 -NoNewline

Write-Host "✓ Dev main.tf updated" -ForegroundColor Green

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Step 4: Update terraform.tfvars" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$devTfvars = @'
aws_region   = "us-east-1"
environment  = "dev"
project_name = "eks-multi-service"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"

availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

public_subnet_cidrs      = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_app_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
private_db_subnet_cidrs  = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

# NAT Gateway Configuration
# Single NAT Gateway for cost optimization in dev (~$32/month vs ~$100/month)
enable_nat_gateway = true
single_nat_gateway = true

# Disable VPC Flow Logs for dev to save costs
enable_flow_logs = false
'@

$devTfvars | Out-File -FilePath "eks-multi-service/terraform/environments/dev/terraform.tfvars" -Encoding UTF8 -NoNewline

Write-Host "✓ terraform.tfvars updated" -ForegroundColor Green

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "Configuration Summary" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host "NAT Gateway: " -NoNewline; Write-Host "Single NAT (cost-optimized)" -ForegroundColor Yellow
Write-Host "Monthly Cost: " -NoNewline; Write-Host "~`$32" -ForegroundColor Yellow
Write-Host "VPC Flow Logs: " -NoNewline; Write-Host "Disabled (saves cost)" -ForegroundColor Yellow
Write-Host "Environments: " -NoNewline; Write-Host "dev, staging, prod" -ForegroundColor Yellow
Write-Host ""
Write-Host "✓ All configuration files updated!" -ForegroundColor Green
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "1. Review changes: git status"
Write-Host "2. Test locally: cd eks-multi-service/terraform/environments/dev; terraform init; terraform plan"
Write-Host "3. Commit changes: git add .; git commit -m 'Configure single NAT Gateway for dev'"
Write-Host "4. Push to trigger deployment: git push origin main"
Write-Host ""