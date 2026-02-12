output "repository_urls" {
  description = "Map of service names to their ECR repository URLs"
  value = {
    for k, v in aws_ecr_repository.services : k => v.repository_url
  }
}

output "repository_arns" {
  description = "Map of service names to their ECR repository ARNs"
  value = {
    for k, v in aws_ecr_repository.services : k => v.arn
  }
}

output "registry_id" {
  description = "The registry ID where the repositories were created"
  value       = data.aws_caller_identity.current.account_id
}

output "registry_url" {
  description = "The URL of the ECR registry"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com"
}

# Individual repository URLs for easy reference
output "frontend_repository_url" {
  description = "ECR repository URL for frontend service"
  value       = aws_ecr_repository.services["frontend"].repository_url
}

output "api_gateway_repository_url" {
  description = "ECR repository URL for API gateway service"
  value       = aws_ecr_repository.services["api-gateway"].repository_url
}

output "auth_service_repository_url" {
  description = "ECR repository URL for auth service"
  value       = aws_ecr_repository.services["auth-service"].repository_url
}

output "product_service_repository_url" {
  description = "ECR repository URL for product service"
  value       = aws_ecr_repository.services["product-service"].repository_url
}

output "order_service_repository_url" {
  description = "ECR repository URL for order service"
  value       = aws_ecr_repository.services["order-service"].repository_url
}

output "payment_service_repository_url" {
  description = "ECR repository URL for payment service"
  value       = aws_ecr_repository.services["payment-service"].repository_url
}
