packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
    ansible = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

locals {
  timestamp  = formatdate("YYYYMMDD-hhmmss", timestamp())
  ami_name   = "${var.ami_prefix}-${local.timestamp}"
  s3_bucket  = regex("s3://([^/]+)/", var.aap_bundle_s3_path)[0]
}

source "amazon-ebs" "rhel9-aap" {
  region        = var.aws_region
  instance_type = var.instance_type

  source_ami_filter {
    filters = {
      name                = var.source_ami_filter_name
      virtualization-type = "hvm"
      architecture        = "x86_64"
      root-device-type    = "ebs"
    }
    owners      = [var.source_ami_owner]
    most_recent = true
  }

  ssh_username = var.ssh_username

  # Network configuration (uses default VPC if empty)
  vpc_id    = var.vpc_id != "" ? var.vpc_id : null
  subnet_id = var.subnet_id != "" ? var.subnet_id : null

  associate_public_ip_address = true

  # Temporary instance profile for S3 access during build (auto-created and deleted)
  temporary_iam_instance_profile_policy_document {
    Statement {
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = ["arn:aws:s3:::${local.s3_bucket}/aap/*"]
    }
    Version = "2012-10-17"
  }

  ami_name        = local.ami_name
  ami_description = "RHEL 9 with Ansible Automation Platform (Controller + Hub + EDA) pre-installed"

  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = var.volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = merge(var.tags, {
    Name        = local.ami_name
    BaseOS      = "RHEL9"
    Application = "AnsibleAutomationPlatform"
    BuildTime   = local.timestamp
  })

  run_tags = merge(var.tags, {
    Name = "packer-builder-aap"
  })
}

build {
  name    = "aap-rhel9"
  sources = ["source.amazon-ebs.rhel9-aap"]

  # Wait for cloud-init to complete before provisioning
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to complete...'",
      "sudo cloud-init status --wait",
      "echo 'Cloud-init complete.'"
    ]
  }

  # Download AAP containerized bundle from S3
  provisioner "shell" {
    inline = [
      "echo 'Downloading AAP containerized bundle from S3...'",
      "sudo dnf install -y awscli2 || sudo dnf install -y aws-cli || pip3 install awscli",
      "aws s3 cp ${var.aap_bundle_s3_path} /tmp/aap-bundle.tar.gz",
      "echo 'AAP bundle downloaded to /tmp/aap-bundle.tar.gz'"
    ]
  }

  # Install required Ansible collections before running the playbook
  provisioner "shell-local" {
    inline = [
      "ansible-galaxy collection install -r ${path.root}/ansible/requirements.yml --force"
    ]
  }

  # Run Ansible playbook for AAP installation
  provisioner "ansible" {
    playbook_file = "${path.root}/ansible/playbook.yml"
    user          = var.ssh_username

    extra_arguments = [
      "--extra-vars", "rhsm_username=${var.rhsm_username}",
      "--extra-vars", "rhsm_password=${var.rhsm_password}",
      "--extra-vars", "aap_admin_password=${var.aap_admin_password}",
      "--scp-extra-args", "'-O'",
      "-v"
    ]

    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SSH_ARGS=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    ]
  }

  # Final cleanup - defense-in-depth to ensure no credentials in AMI
  provisioner "shell" {
    inline = [
      "echo 'Final AMI preparation...'",
      "sudo cloud-init clean --logs --seed",
      "sudo rm -rf /tmp/* /var/tmp/*",
      "sudo rm -f /root/.bash_history",
      "sudo rm -f /home/${var.ssh_username}/.bash_history",
      "sudo rm -rf /var/log/journal/*",
      "sudo truncate -s 0 /var/log/messages /var/log/secure /var/log/audit/audit.log || true",
      "echo 'AMI preparation complete.'"
    ]
  }

  post-processor "manifest" {
    output     = "packer-manifest.json"
    strip_path = true
  }
}
