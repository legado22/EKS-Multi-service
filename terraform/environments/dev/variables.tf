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

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = false
}

variable "single_nat_gateway" {
  description = "usage of single nat gateway"
  type        = bool
  default     = false

}

variable "cluster_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.29"
}

# EKS Node Group Variables
variable "node_group_name" {
  description = "Name of the EKS node group"
  type        = string
  default     = "general"
}

variable "node_instance_types" {
  description = "List of instance types for the node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_disk_size" {
  description = "Disk size in GB for worker nodes"
  type        = number
  default     = 20
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

# EKS Cluster Logging Variables
variable "enable_cluster_logging" {
  description = "Enable EKS control plane logging"
  type        = bool
  default     = false
}

variable "cluster_log_retention_days" {
  description = "Number of days to retain cluster logs"
  type        = number
  default     = 7
}

# EKS IRSA Variable
variable "enable_irsa" {
  description = "Enable IAM Roles for Service Accounts"
  type        = bool
  default     = true
}

# ECR Variables
variable "ecr_scan_on_push" {
  description = "Indicates whether images are scanned after being pushed to the repository"
  type        = bool
  default     = true
}

variable "ecr_image_retention_count" {
  description = "Number of tagged images to retain"
  type        = number
  default     = 10
}

variable "ecr_untagged_retention_days" {
  description = "Number of days to retain untagged images before deletion"
  type        = number
  default     = 7
}

variable "ecr_enable_replication" {
  description = "Enable cross-region replication for disaster recovery"
  type        = bool
  default     = false
}

variable "packer_s3_bucket" {
  description = "S3 bucket name where the AAP bundle is stored"
  type        = string
  default     = ""
}

# AAP EC2 Variables
variable "aap_ami_id" {
  description = "AMI ID from Packer build for AAP. Set to null to use dynamic RHEL 9 lookup."
  type        = string
  default     = null
}

variable "aap_instance_type" {
  description = "EC2 instance type for AAP (minimum t3.2xlarge for 8 vCPU, 32GB RAM)"
  type        = string
  default     = "t3.2xlarge"
}

variable "aap_root_volume_size" {
  description = "Root volume size in GB for AAP instance"
  type        = number
  default     = 200
}

variable "aap_key_name" {
  description = "SSH key pair name for AAP instance"
  type        = string
  default     = null
}

variable "aap_allowed_cidrs" {
  description = "CIDR blocks allowed to access AAP web interfaces (443, 8443)"
  type        = list(string)
  default = [] # Set in terraform.tfvars
}

variable "aap_allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH into AAP instance"
  type        = list(string)
  default     = [] # Set in terraform.tfvars
}
