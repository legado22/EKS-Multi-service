variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"

}

variable "state_bucket_name" {
  description = "s3 bucket name for terraform state"
  type        = string
}

variable "dynamodb_table_name" {
  description = "dynamoDB name for state locking"
  type        = string
  default     = "terraform-state-lock"
}
