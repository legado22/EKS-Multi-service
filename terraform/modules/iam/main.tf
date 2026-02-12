# IAM Users
resource "aws_iam_user" "users" {
  for_each = var.iam_users

  name = each.key
  path = each.value.path

  tags = merge(
    var.tags,
    {
      Name        = each.key
      Environment = var.environment
    }
  )
}

# IAM User Policies
resource "aws_iam_user_policy_attachment" "user_policies" {
  for_each = {
    for combo in flatten([
      for user, config in var.iam_users : [
        for policy in config.policies : {
          user   = user
          policy = policy
          key    = "${user}-${policy}"
        }
      ]
    ]) : combo.key => combo
  }

  user       = aws_iam_user.users[each.value.user].name
  policy_arn = each.value.policy
}

# GitHub Actions OIDC Provider
resource "aws_iam_openid_connect_provider" "github_actions" {
  count = var.enable_github_actions ? 1 : 0

  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-github-actions-oidc"
      Environment = var.environment
    }
  )
}

# GitHub Actions Role
resource "aws_iam_role" "github_actions" {
  count = var.enable_github_actions ? 1 : 0

  name        = "${var.project_name}-${var.environment}-github-actions-role"
  description = "Role for GitHub Actions to manage EKS infrastructure"
  path        = "/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions[0].arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-github-actions-role"
      Environment = var.environment
    }
  )
}

# GitHub Actions Role Policies
resource "aws_iam_role_policy_attachment" "github_actions_policies" {
  for_each = var.enable_github_actions ? toset(var.github_actions_policies) : toset([])

  role       = aws_iam_role.github_actions[0].name
  policy_arn = each.value
}

# Inline policy for ECR repository policy management
resource "aws_iam_role_policy" "github_actions_ecr_policy" {
  count = var.enable_github_actions ? 1 : 0

  name = "ecr-repository-policy-management"
  role = aws_iam_role.github_actions[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:SetRepositoryPolicy",
          "ecr:DeleteRepositoryPolicy",
          "ecr:GetRepositoryPolicy"
        ]
        Resource = "*"
      }
    ]
  })
}

# Inline policy for EKS cluster management
resource "aws_iam_role_policy" "github_actions_eks_policy" {
  count = var.enable_github_actions ? 1 : 0

  name = "eks-cluster-management"
  role = aws_iam_role.github_actions[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "eks:CreateCluster",
          "eks:DeleteCluster",
          "eks:DescribeCluster",
          "eks:UpdateClusterConfig",
          "eks:UpdateClusterVersion",
          "eks:CreateNodegroup",
          "eks:DeleteNodegroup",
          "eks:DescribeNodegroup",
          "eks:UpdateNodegroupConfig",
          "eks:UpdateNodegroupVersion",
          "eks:ListClusters",
          "eks:ListNodegroups",
          "eks:TagResource",
          "eks:UntagResource",
          "eks:CreateAddon",
          "eks:DeleteAddon",
          "eks:DescribeAddon",
          "eks:UpdateAddon",
          "eks:ListAddons",
          "eks:DescribeAddonVersions"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "eks.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Inline policy for Packer AAP bundle access
resource "aws_iam_role_policy" "github_actions_packer_s3_policy" {
  count = var.enable_github_actions ? 1 : 0

  name = "packer-aap-bundle-s3-access"
  role = aws_iam_role.github_actions[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::${var.packer_s3_bucket}/aap/*"
      }
    ]
  })
}

# Custom IAM Roles
resource "aws_iam_role" "custom_roles" {
  for_each = var.custom_roles

  name        = each.key
  description = each.value.description
  path        = each.value.path

  assume_role_policy = each.value.assume_role_policy

  tags = merge(
    var.tags,
    {
      Name        = each.key
      Environment = var.environment
    }
  )
}

# Custom Role Policy Attachments
resource "aws_iam_role_policy_attachment" "custom_role_policies" {
  for_each = {
    for combo in flatten([
      for role, config in var.custom_roles : [
        for policy in config.policies : {
          role   = role
          policy = policy
          key    = "${role}-${policy}"
        }
      ]
    ]) : combo.key => combo
  }

  role       = aws_iam_role.custom_roles[each.value.role].name
  policy_arn = each.value.policy
}

# IAM Policies (Custom)
resource "aws_iam_policy" "custom_policies" {
  for_each = var.custom_policies

  name        = each.key
  description = each.value.description
  path        = each.value.path
  policy      = each.value.policy

  tags = merge(
    var.tags,
    {
      Name        = each.key
      Environment = var.environment
    }
  )
}
