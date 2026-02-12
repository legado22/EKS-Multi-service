# Data source to get the latest RHEL 9 AMI (skipped when custom AMI is provided)
data "aws_ami" "rhel9" {
  count       = var.custom_ami_id == null ? 1 : 0
  most_recent = true
  owners      = ["309956199498"] # Red Hat's AWS account ID

  filter {
    name   = "name"
    values = ["RHEL-9.*_HVM-*-x86_64-*-Hourly2-GP3"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

locals {
  ami_id      = var.custom_ami_id != null ? var.custom_ami_id : data.aws_ami.rhel9[0].id
  is_prebaked = var.custom_ami_id != null
}

# Security Group for EC2 instance
resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for EC2 instance with SSH access"
  vpc_id      = var.vpc_id

  # SSH access from allowed IPs
  dynamic "ingress" {
    for_each = var.allowed_ssh_cidrs
    content {
      description = "SSH from ${ingress.value}"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  # AAP Controller Web UI (HTTPS)
  dynamic "ingress" {
    for_each = var.enable_aap_ports ? var.allowed_aap_cidrs : []
    content {
      description = "AAP Controller HTTPS from ${ingress.value}"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  # AAP Hub Web UI
  dynamic "ingress" {
    for_each = var.enable_aap_ports ? var.allowed_aap_cidrs : []
    content {
      description = "AAP Hub HTTPS from ${ingress.value}"
      from_port   = 8443
      to_port     = 8443
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  # Receptor mesh port (VPC internal only)
  dynamic "ingress" {
    for_each = var.enable_aap_ports ? [var.vpc_cidr] : []
    content {
      description = "Receptor mesh from VPC"
      from_port   = 27199
      to_port     = 27199
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  # PostgreSQL (VPC internal only)
  dynamic "ingress" {
    for_each = var.enable_aap_ports ? [var.vpc_cidr] : []
    content {
      description = "PostgreSQL from VPC"
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ec2-sg"
    }
  )
}

# EC2 Instance
resource "aws_instance" "main" {
  ami                         = local.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.ec2.id]
  key_name                    = var.key_name
  associate_public_ip_address = var.associate_public_ip

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true

    tags = merge(
      var.tags,
      {
        Name = "${var.project_name}-ec2-root-volume"
      }
    )
  }

  user_data = local.is_prebaked ? base64encode(<<-EOF
    #!/bin/bash
    # Pre-baked AAP AMI - first-boot preparation
    # Do NOT override hostname - let cloud-init set the proper AWS hostname
    # so the aap-firstboot service can detect the change and reconfigure AAP.
    set -e

    # Regenerate SSH host keys if needed
    if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
      ssh-keygen -A
      systemctl restart sshd
    fi

    # === Pre-cleanup: reset AAP containers/volumes for clean firstboot ===
    # The firstboot service (After=cloud-init.service) will re-run the AAP
    # installer. This cleanup ensures old TLS certs in Podman volumes are
    # removed so the installer generates fresh certs for the new hostname.
    AAP_USER="ec2-user"
    AAP_UID=$(id -u "$AAP_USER" 2>/dev/null || echo "1000")

    # Ensure user runtime directory exists for rootless Podman
    if [ ! -d "/run/user/$AAP_UID" ]; then
      mkdir -p "/run/user/$AAP_UID"
      chown "$AAP_USER:$AAP_USER" "/run/user/$AAP_UID"
      chmod 700 "/run/user/$AAP_UID"
    fi
    loginctl enable-linger "$AAP_USER" 2>/dev/null || true

    su - "$AAP_USER" -c "
      export XDG_RUNTIME_DIR=/run/user/$AAP_UID
      systemctl --user stop 'automation-*' 'receptor*' 'redis*' 'postgresql*' 2>/dev/null || true
      podman stop -a -t 10 2>/dev/null || true
      podman rm -a -f 2>/dev/null || true
      podman volume rm -a -f 2>/dev/null || true
      systemctl --user disable 'automation-*' 'receptor*' 'redis*' 'postgresql*' 2>/dev/null || true
      systemctl --user daemon-reload 2>/dev/null || true
    " || true

    rm -rf "/home/$AAP_USER/aap"
    echo "Pre-cleanup complete."

    # === Fix systemd ordering cycle in old AMIs ===
    # AMIs built before the fix have After=cloud-final.service which creates
    # a cycle with multi-user.target. Patch the service file and start it manually.
    SVC_FILE="/etc/systemd/system/aap-firstboot.service"
    if grep -q "cloud-final.service" "$SVC_FILE" 2>/dev/null; then
      echo "Patching aap-firstboot.service to fix systemd ordering cycle..."
      sed -i 's/cloud-final.service/cloud-init.service/' "$SVC_FILE"
      systemctl daemon-reload
    fi
    # Start firstboot manually since cloud-init user scripts run after multi-user.target
    echo "Starting aap-firstboot service..."
    systemctl start aap-firstboot &
  EOF
  ) : base64encode(<<-EOF
    #!/bin/bash
    set -e

    # Create user with password
    useradd -m -s /bin/bash ${var.ssh_username}
    echo "${var.ssh_username}:${var.ssh_password}" | chpasswd

    # Add user to wheel group for sudo access
    usermod -aG wheel ${var.ssh_username}

    # Enable password authentication for SSH
    sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

    # Ensure PasswordAuthentication is set to yes
    if ! grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
      echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
    fi

    # Restart SSH service
    systemctl restart sshd

    # Update the system
    dnf update -y
  EOF
  )

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ec2"
    }
  )

  lifecycle {
    ignore_changes = [ami]
  }
}
