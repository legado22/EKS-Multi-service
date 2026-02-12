output "user_arns" {
  description = "ARNs of created IAM users"
  value       = { for k, v in aws_iam_user.users : k => v.arn }
}

output "user_names" {
  description = "Names of created IAM users"
  value       = { for k, v in aws_iam_user.users : k => v.name }
}

output "github_actions_role_arn" {
  description = "ARN of GitHub Actions role"
  value       = var.enable_github_actions ? aws_iam_role.github_actions[0].arn : null
}

output "github_actions_role_name" {
  description = "Name of GitHub Actions role"
  value       = var.enable_github_actions ? aws_iam_role.github_actions[0].name : null
}

output "github_actions_oidc_provider_arn" {
  description = "ARN of GitHub Actions OIDC provider"
  value       = var.enable_github_actions ? aws_iam_openid_connect_provider.github_actions[0].arn : null
}

output "custom_role_arns" {
  description = "ARNs of custom IAM roles"
  value       = { for k, v in aws_iam_role.custom_roles : k => v.arn }
}

output "custom_role_names" {
  description = "Names of custom IAM roles"
  value       = { for k, v in aws_iam_role.custom_roles : k => v.name }
}

output "custom_policy_arns" {
  description = "ARNs of custom IAM policies"
  value       = { for k, v in aws_iam_policy.custom_policies : k => v.arn }
}

output "custom_policy_names" {
  description = "Names of custom IAM policies"
  value       = { for k, v in aws_iam_policy.custom_policies : k => v.name }
}
