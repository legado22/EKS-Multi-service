variable "project_name" {
  description = "Project name to be used as a prefix"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "iam_users" {
  description = "Map of IAM users to create"
  type = map(object({
    path     = string
    policies = list(string)
  }))
  default = {}
}

variable "enable_github_actions" {
  description = "Enable GitHub Actions OIDC provider and role"
  type        = bool
  default     = false
}

variable "github_repo" {
  description = "GitHub repository in the format 'owner/repo'"
  type        = string
  default     = ""
}

variable "github_actions_policies" {
  description = "List of IAM policy ARNs to attach to GitHub Actions role"
  type        = list(string)
  default = [
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    "arn:aws:iam::aws:policy/AmazonVPCFullAccess",
    "arn:aws:iam::aws:policy/IAMFullAccess"
  ]
}

variable "custom_roles" {
  description = "Map of custom IAM roles to create"
  type = map(object({
    description        = string
    path               = string
    assume_role_policy = string
    policies           = list(string)
  }))
  default = {}
}

variable "custom_policies" {
  description = "Map of custom IAM policies to create"
  type = map(object({
    description = string
    path        = string
    policy      = string
  }))
  default = {}
}

variable "packer_s3_bucket" {
  description = "S3 bucket name where the AAP bundle is stored"
  type        = string
  default     = ""
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}
