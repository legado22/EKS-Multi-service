# IAM Module

This module manages IAM resources for the EKS multi-service infrastructure.

## Features

- **IAM Users**: Create and manage IAM users with policy attachments
- **GitHub Actions OIDC**: Setup OIDC provider and role for GitHub Actions CI/CD
- **Custom Roles**: Create custom IAM roles with assume role policies
- **Custom Policies**: Define and attach custom IAM policies

## Usage

```hcl
module "iam" {
  source = "../../modules/iam"

  project_name = "eks-multi-service"
  environment  = "dev"

  # IAM Users
  iam_users = {
    legado = {
      path = "/"
      policies = [
        "arn:aws:iam::aws:policy/AdministratorAccess"
      ]
    }
  }

  # GitHub Actions
  enable_github_actions = true
  github_repo          = "masterminders-maker/kubernetes-terra"

  github_actions_policies = [
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    "arn:aws:iam::aws:policy/AmazonVPCFullAccess",
    "arn:aws:iam::aws:policy/IAMFullAccess"
  ]

  tags = {
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}
```

## Existing Resources

This module can manage the following existing IAM resources in your AWS account:

### IAM Users
- **legado** (Created: 2026-01-24)

### IAM Roles
- **GitHubActionsRole-EKS-MultiService** - For GitHub Actions CI/CD

### Service-Linked Roles (Managed by AWS)
These are automatically created by AWS services and should not be managed in Terraform:
- AWSServiceRoleForAmazonEKS
- AWSServiceRoleForAmazonEKSNodegroup
- AWSServiceRoleForAutoScaling
- AWSServiceRoleForResourceExplorer
- AWSServiceRoleForSupport
- AWSServiceRoleForTrustedAdvisor

### EKS-Managed Roles (Created by EKS Module)
These roles are managed by the EKS module:
- eks-multi-service-dev-cluster-role
- eks-multi-service-dev-node-group-role
- eks-multi-service-dev-ebs-csi-driver

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Project name to be used as a prefix | `string` | n/a | yes |
| environment | Environment name (dev, staging, prod) | `string` | n/a | yes |
| iam_users | Map of IAM users to create | `map(object)` | `{}` | no |
| enable_github_actions | Enable GitHub Actions OIDC provider and role | `bool` | `false` | no |
| github_repo | GitHub repository in the format 'owner/repo' | `string` | `""` | no |
| github_actions_policies | List of IAM policy ARNs to attach to GitHub Actions role | `list(string)` | See variables.tf | no |
| custom_roles | Map of custom IAM roles to create | `map(object)` | `{}` | no |
| custom_policies | Map of custom IAM policies to create | `map(object)` | `{}` | no |
| tags | A map of tags to add to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| user_arns | ARNs of created IAM users |
| user_names | Names of created IAM users |
| github_actions_role_arn | ARN of GitHub Actions role |
| github_actions_role_name | Name of GitHub Actions role |
| github_actions_oidc_provider_arn | ARN of GitHub Actions OIDC provider |
| custom_role_arns | ARNs of custom IAM roles |
| custom_role_names | Names of custom IAM roles |
| custom_policy_arns | ARNs of custom IAM policies |
| custom_policy_names | Names of custom IAM policies |

## Important Notes

1. **Service-Linked Roles**: Do not attempt to manage AWS service-linked roles in Terraform. They are automatically created and managed by AWS.

2. **EKS Roles**: The EKS-specific roles (cluster-role, node-group-role, ebs-csi-driver) are created by the EKS module and should not be duplicated here.

3. **Import Existing Resources**: If you have existing IAM resources, import them using:
   ```bash
   terraform import module.iam.aws_iam_user.users[\"legado\"] legado
   ```

4. **GitHub Actions**: The OIDC provider enables GitHub Actions to assume AWS roles without storing long-term credentials.

## Example: Import Existing User

```bash
cd terraform/environments/dev
terraform import module.iam.aws_iam_user.users[\"legado\"] legado
```
