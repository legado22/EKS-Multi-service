module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  cluster_name = "${var.project_name}-${var.environment}"
  vpc_cidr     = var.vpc_cidr

  availability_zones       = var.availability_zones
  public_subnet_cidrs      = var.public_subnet_cidrs
  private_app_subnet_cidrs = var.private_app_subnet_cidrs
  private_db_subnet_cidrs  = var.private_db_subnet_cidrs

  enable_nat_gateway = var.enable_nat_gateway
  enable_flow_logs   = var.enable_flow_logs
  single_nat_gateway = var.single_nat_gateway

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}


# EKS Module - Temporarily disabled to save costs
# Uncomment when ready to redeploy
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.cluster_version

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_app_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids

  node_group_name     = var.node_group_name
  node_instance_types = var.node_instance_types
  node_disk_size      = var.node_disk_size
  node_desired_size   = var.node_desired_size
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size

  enable_cluster_logging     = var.enable_cluster_logging
  cluster_log_retention_days = var.cluster_log_retention_days
  enable_irsa                = var.enable_irsa

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [module.vpc]
}


module "iam" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = var.environment

  # IAM Users
  iam_users = {
    legado = {
      path = "/"
      policies = [
        "arn:aws:iam::aws:policy/AdministratorAccess"
      ]
    }
  }

  # GitHub Actions OIDC
  enable_github_actions = true
  github_repo           = "masterminders-maker/kubernetes-terra"

  github_actions_policies = [
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    "arn:aws:iam::aws:policy/AmazonVPCFullAccess",
    "arn:aws:iam::aws:policy/IAMFullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"

  ]

  packer_s3_bucket = var.packer_s3_bucket

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}


module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name

  # Image scanning and retention
  scan_on_push                  = var.ecr_scan_on_push
  image_retention_count         = var.ecr_image_retention_count
  untagged_image_retention_days = var.ecr_untagged_retention_days

  # Allow EKS nodes to pull images (disabled while EKS is destroyed)
  allowed_read_principals = [module.eks.node_group_iam_role_arn]

  # Replication for production (disabled in dev)
  enable_replication = var.ecr_enable_replication

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  # depends_on = [module.eks]
}


# AAP EC2 Instance - Ansible Automation Platform
module "ec2_aap" {
  source = "../../modules/ec2"

  project_name = "${var.project_name}-aap"
  vpc_id       = module.vpc.vpc_id
  subnet_id    = module.vpc.public_subnet_ids[0]

  # Use pre-baked AAP AMI (set after Packer build)
  custom_ami_id    = var.aap_ami_id
  instance_type    = var.aap_instance_type
  root_volume_size = var.aap_root_volume_size

  # AAP networking
  enable_aap_ports  = true
  allowed_aap_cidrs = var.aap_allowed_cidrs
  vpc_cidr          = var.vpc_cidr
  allowed_ssh_cidrs = var.aap_allowed_ssh_cidrs
  key_name          = var.aap_key_name

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Component   = "AAP"
  }

  depends_on = [module.vpc]
}
