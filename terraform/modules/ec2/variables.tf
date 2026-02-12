variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the EC2 instance will be created"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type (default t3.2xlarge for AAP: 8 vCPU, 32GB RAM)"
  type        = string
  default     = "t3.2xlarge"
}

variable "root_volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 200
}

variable "ssh_username" {
  description = "Username for SSH access"
  type        = string
  default     = "adminuser"
}

variable "ssh_password" {
  description = "Password for SSH access (will be set via cloud-init). Not required for pre-baked AMIs."
  type        = string
  sensitive   = true
  default     = null
}

variable "allowed_ssh_cidrs" {
  description = "List of CIDR blocks allowed to SSH into the instance"
  type        = list(string)
  default = []
}

variable "key_name" {
  description = "Name of the SSH key pair (optional, password auth will also be enabled)"
  type        = string
  default     = null
}

variable "associate_public_ip" {
  description = "Whether to associate a public IP address"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "custom_ami_id" {
  description = "Optional custom AMI ID (e.g., Packer-built AAP AMI). When set, the dynamic RHEL 9 lookup is skipped."
  type        = string
  default     = null
}

variable "enable_aap_ports" {
  description = "Enable AAP-specific security group rules (443, 8443, 27199, 5432)"
  type        = bool
  default     = false
}

variable "allowed_aap_cidrs" {
  description = "CIDR blocks allowed to access AAP web interfaces (443, 8443)"
  type        = list(string)
  default     = []
}

variable "vpc_cidr" {
  description = "VPC CIDR block for internal service ports (receptor, PostgreSQL)"
  type        = string
  default     = "10.0.0.0/16"
}
