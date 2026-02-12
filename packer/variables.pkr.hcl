variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region to build the AMI in"
}

variable "instance_type" {
  type        = string
  default     = "t3.2xlarge"
  description = "Instance type for the Packer builder (8 vCPU, 32GB RAM for full AAP)"
}

variable "source_ami_filter_name" {
  type        = string
  default     = "RHEL-9.*_HVM-*-x86_64-*-Hourly2-GP3"
  description = "AMI name filter for RHEL 9 source AMI (matches EC2 module)"
}

variable "source_ami_owner" {
  type        = string
  default     = "309956199498"
  description = "Red Hat AWS account ID for AMI ownership"
}

variable "rhsm_username" {
  type        = string
  sensitive   = true
  description = "Red Hat Subscription Manager username (Red Hat account email)"
}

variable "rhsm_password" {
  type        = string
  sensitive   = true
  description = "Red Hat Subscription Manager password"
}

variable "aap_admin_password" {
  type        = string
  sensitive   = true
  default     = "changeme"
  description = "Initial admin password for AAP Controller (change on first login)"
}

variable "ssh_username" {
  type        = string
  default     = "ec2-user"
  description = "SSH username for the Packer builder (RHEL 9 default)"
}

variable "ami_prefix" {
  type        = string
  default     = "eks-multi-service-aap"
  description = "Prefix for the AMI name"
}

variable "volume_size" {
  type        = number
  default     = 200
  description = "Root volume size in GB for the AMI"
}

variable "vpc_id" {
  type        = string
  default     = ""
  description = "Optional VPC ID for the builder instance. Empty uses default VPC."
}

variable "subnet_id" {
  type        = string
  default     = ""
  description = "Optional subnet ID for the builder instance. Empty uses default."
}

variable "aap_bundle_s3_path" {
  type        = string
  default     = "s3://your-s3-bucket/aap/ansible-automation-platform-containerized-setup-bundle-2.6-5-x86_64.tar.gz"
  description = "S3 path to the AAP containerized setup bundle tarball"
}

variable "tags" {
  type = map(string)
  default = {
    Project   = "eks-multi-service"
    ManagedBy = "Packer"
    Component = "AAP"
  }
}
