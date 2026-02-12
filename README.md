# EKS Multi-Service Infrastructure

> **Auto-generated documentation** - Last updated: 2026-01-23 22:49 UTC

[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-EKS-orange)](https://aws.amazon.com/eks/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

Production-ready, multi-environment Kubernetes infrastructure on AWS EKS with complete automation via GitHub Actions.

##  Infrastructure Overview

**Current Status:**
- **Environments:** 1 (dev)
- **Terraform Modules:** 4 (vpc, eks, iam, ecr)
- **CI/CD Pipelines:** 1 workflow (Terraform Dev)
- **Cloud Provider:** AWS (us-east-1)
- **Orchestration:** Amazon EKS + Terraform
- **EKS Cluster:**  **DISABLED** (cost savings mode)

##  EKS Cluster Status

The EKS cluster is currently **disabled** to save costs (~$170+/month). The following infrastructure remains active:

| Resource | Status | Est. Cost |
|----------|--------|-----------|
| VPC + Subnets |  Active | ~$0 |
| NAT Gateway (single) |  Active | ~$32/month |
| ECR Repositories |  Active | < $1/month |
| IAM Roles & Users |  Active | $0 |
| **EKS Cluster** |  Disabled | $0 |
| **EKS Node Group** |  Disabled | $0 |

### Redeploy EKS Cluster

To redeploy the EKS cluster when needed:

**Step 1:** Uncomment the EKS module in `terraform/environments/dev/main.tf`:

```hcl
# Uncomment lines 25-55:
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.cluster_version
  # ... rest of configuration
}
```

**Step 2:** Uncomment the ECR allowed_read_principals in the same file:

```hcl
# Change line 107 from:
allowed_read_principals = []

# To:
allowed_read_principals = [module.eks.node_group_iam_role_arn]
```

**Step 3:** Commit and push to trigger GitHub Actions:

```bash
git add .
git commit -m "Enable EKS cluster"
git push origin main
```

The workflow will automatically deploy the EKS cluster (takes ~15-20 minutes).

### Disable EKS Cluster (Cost Savings)

To disable the EKS cluster and save costs:

1. Comment out the EKS module (lines 25-55) in `terraform/environments/dev/main.tf`
2. Set `allowed_read_principals = []` in the ECR module
3. Commit and push - GitHub Actions will destroy the EKS resources

##  Quick Start

### Prerequisites
```bash
# Required tools
terraform >= 1.6.0
kubectl >= 1.28.0
aws-cli >= 2.13.0
```

### Deploy Infrastructure

**Option 1: GitHub Actions (Recommended)**
```bash
# Push changes to main branch
git add .
git commit -m "Deploy infrastructure"
git push origin main
# Workflow automatically triggers for dev environment
```

**Option 2: Local Deployment**
```bash
cd eks-multi-service/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

**Option 3: Manual Workflow Trigger**
- Go to: Actions → Terraform Staging/Prod
- Click "Run workflow"
- Select: plan or apply

##  Infrastructure Environments

### DEV Environment

**Configuration:**
```hcl
availability_zones             = ["us-east-1a", "us-east-1b", "us-east-1c"]
aws_region                     = us-east-1
enable_flow_logs               = false
enable_nat_gateway             = true
environment                    = dev
private_app_subnet_cidrs       = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
private_db_subnet_cidrs        = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
project_name                   = eks-multi-service
public_subnet_cidrs            = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
single_nat_gateway             = true # Use single NAT Gateway for all private subnets
vpc_cidr                       = 10.0.0.0/16
```

**Estimated Cost:** ~$96/month


##  CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| Terraform Dev | Push to main, PR to main, Manual | Automatically deploys dev environment infrastructure |

##  Cost Breakdown

### Current Cost (EKS Disabled)
| Resource | Estimated Monthly Cost |
|----------|------------------------|
| NAT Gateway (single) | ~$32 |
| ECR Storage | < $1 |
| **Total** | **~$33/month** |

### Full Cost (EKS Enabled)
| Resource | Estimated Monthly Cost |
|----------|------------------------|
| NAT Gateway (single) | ~$32 |
| EKS Control Plane | ~$73 |
| EKS Nodes (3x t3.medium) | ~$100 |
| ECR Storage | < $1 |
| **Total** | **~$206/month** |

*Note: Actual costs may vary based on data transfer, storage, and usage.*

##  Terraform Modules

### VPC Module

**Creates:**
- Cloudwatch Log Group
- Eip
- Flow Log
- Iam Role
- Iam Role Policy
- Internet Gateway
- Nat Gateway
- Route Table
- Route Table Association
- Subnet
- Vpc

<details>
<summary> Input Variables</summary>

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `project_name` | string | Project name to be used as a prefix | None |
| `cluster_name` | string | EKS cluster name for subnet tagging | None |
| `vpc_cidr` | string | CIDR block for VPC | "10.0.0.0/16" |
| `availability_zones` | list | List of availability zones | None |
| `public_subnet_cidrs` | list | CIDR blocks for public subnets | None |
| `private_app_subnet_cidrs` | list | CIDR blocks for private application subnets | None |
| `private_db_subnet_cidrs` | list | CIDR blocks for private database subnets | None |
| `enable_nat_gateway` | bool | Enable NAT Gateway for private subnets | true |
| `single_nat_gateway` | bool | Use a single NAT Gateway for all private subnets (cost optimization) | false |
| `enable_flow_logs` | bool | Enable VPC Flow Logs | true |
</details>

<details>
<summary> Outputs</summary>

| Output | Description |
|--------|-------------|
| `vpc_id` | The ID of the VPC |
| `vpc_cidr` | The CIDR block of the VPC |
| `public_subnet_ids` | List of IDs of public subnets |
| `private_app_subnet_ids` | List of IDs of private application subnets |
| `private_db_subnet_ids` | List of IDs of private database subnets |
| `nat_gateway_ids` | List of NAT Gateway IDs |
| `internet_gateway_id` | ID of the Internet Gateway |
</details>

### EKS Module

**Creates:**
- Cloudwatch Log Group
- Eks Addon
- Eks Cluster
- Eks Node Group
- Iam Openid Connect Provider
- Iam Role
- Iam Role Policy Attachment
- Security Group
- Security Group Rule

<details>
<summary> Input Variables</summary>

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `cluster_name` | string | Name of the EKS cluster | None |
| `cluster_version` | string | Kubernetes version to use for the EKS cluster | "1.29" |
| `vpc_id` | string | VPC ID where the cluster will be created | None |
| `private_subnet_ids` | list | List of private subnet IDs for the EKS cluster | None |
| `public_subnet_ids` | list | List of public subnet IDs for the EKS cluster load balancers | None |
| `node_group_name` | string | Name of the EKS node group | "general" |
| `node_instance_types` | list | List of instance types for the node group | ["t3.medium"] |
| `node_disk_size` | number | Disk size in GB for worker nodes | 20 |
| `node_desired_size` | number | Desired number of worker nodes | 3 |
| `node_min_size` | number | Minimum number of worker nodes | 2 |
</details>

<details>
<summary> Outputs</summary>

| Output | Description |
|--------|-------------|
| `cluster_id` | The name/id of the EKS cluster |
| `cluster_arn` | The Amazon Resource Name (ARN) of the cluster |
| `cluster_endpoint` | Endpoint for EKS control plane |
| `cluster_version` | The Kubernetes server version for the cluster |
| `cluster_security_group_id` | Security group ID attached to the EKS cluster |
| `node_security_group_id` | Security group ID attached to the EKS nodes |
| `cluster_iam_role_arn` | IAM role ARN of the EKS cluster |
| `node_group_iam_role_arn` | IAM role ARN of the EKS node group |
| `cluster_certificate_authority_data` | Base64 encoded certificate data required to communicate with the cluster |
| `cluster_oidc_issuer_url` | The URL on the EKS cluster OIDC Issuer |
| `oidc_provider_arn` | ARN of the OIDC Provider for EKS |
| `node_group_id` | EKS node group ID |
| `node_group_status` | Status of the EKS node group |
| `node_group_asg_name` | Name of the Auto Scaling Group associated with the EKS node group |
| `kubeconfig_command` | Command to update kubeconfig |
</details>

### IAM Module

**Creates:**
- Iam User
- Iam User Policy Attachment
- Iam Openid Connect Provider (GitHub Actions)
- Iam Role (GitHub Actions)
- Iam Role Policy Attachment
- Custom Iam Roles
- Custom Iam Policies

<details>
<summary> Input Variables</summary>

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `project_name` | string | Project name to be used as a prefix | None |
| `environment` | string | Environment name (dev, staging, prod) | None |
| `iam_users` | map(object) | Map of IAM users to create with policy attachments | {} |
| `enable_github_actions` | bool | Enable GitHub Actions OIDC provider and role | false |
| `github_repo` | string | GitHub repository in the format 'owner/repo' | "" |
| `github_actions_policies` | list(string) | List of IAM policy ARNs to attach to GitHub Actions role | See module |
| `custom_roles` | map(object) | Map of custom IAM roles to create | {} |
| `custom_policies` | map(object) | Map of custom IAM policies to create | {} |
</details>

<details>
<summary> Outputs</summary>

| Output | Description |
|--------|-------------|
| `user_arns` | ARNs of created IAM users |
| `user_names` | Names of created IAM users |
| `github_actions_role_arn` | ARN of GitHub Actions role |
| `github_actions_role_name` | Name of GitHub Actions role |
| `github_actions_oidc_provider_arn` | ARN of GitHub Actions OIDC provider |
| `custom_role_arns` | ARNs of custom IAM roles |
| `custom_role_names` | Names of custom IAM roles |
| `custom_policy_arns` | ARNs of custom IAM policies |
| `custom_policy_names` | Names of custom IAM policies |
</details>

**Key Features:**
- **IAM User Management**: Create and manage IAM users with policy attachments
- **GitHub Actions OIDC**: Secure, keyless authentication for CI/CD pipelines
- **Custom Roles & Policies**: Flexible IAM role and policy management
- **AWS Service Integration**: Compatible with EKS, VPC, and other AWS services


##  Additional Documentation

- [Terraform Modules](terraform/modules/README.md)
- [Deployment Guide](docs/deployment-guide.md)
- [Troubleshooting](docs/troubleshooting.md)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

##  Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

##  License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

##  Acknowledgments

- AWS EKS team for comprehensive documentation
- Terraform community for infrastructure patterns
- GitHub Actions for CI/CD automation

---

** This README is automatically generated.** To update, modify infrastructure code and push to main branch.
