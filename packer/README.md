# Packer AMI Build: Containerized Ansible Automation Platform on RHEL 9

Pre-bakes a RHEL 9 AMI with the full Ansible Automation Platform 2.6 (Controller + Hub + EDA) running as rootless Podman containers. The AMI includes a first-boot reconfiguration service that automatically detects hostname changes and regenerates TLS certificates, making the image portable across AWS accounts, VPCs, vCenter, and bare metal.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Build the AMI](#build-the-ami)
- [Deploy with Terraform](#deploy-with-terraform)
- [First-Boot Reconfiguration](#first-boot-reconfiguration)
- [AAP Access](#aap-access)
- [CI/CD Pipeline](#cicd-pipeline)
- [Multi-Platform Support](#multi-platform-support)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Project Structure](#project-structure)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Packer Build                          │
│                                                         │
│  ┌──────┐  ┌───────────┐  ┌─────────┐  ┌───────────┐  │
│  │ rhsm │→ │aap-prereqs│→ │aap-inst.│→ │aap-first- │  │
│  │      │  │           │  │         │  │   boot     │  │
│  └──────┘  └───────────┘  └─────────┘  └───────────┘  │
│      │          │              │             │          │
│  Subscribe  Install         Run AAP      Install       │
│  to RHSM    Podman,        installer     firstboot     │
│             ansible-core   (Podman)      systemd svc   │
│                                                         │
│  ┌─────────┐                                            │
│  │ cleanup │ → Unsubscribe RHSM, remove secrets,       │
│  │         │   clean logs, remove SSH host keys         │
│  └─────────┘                                            │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   AMI Snapshot   │
               │   (~200GB GP3)   │
               └─────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              EC2 Instance Launch                         │
│                                                         │
│  1. cloud-init sets hostname from DHCP/metadata         │
│  2. aap-firstboot.service detects hostname change       │
│  3. Cleans old containers, volumes, TLS certs           │
│  4. Re-runs AAP installer with correct hostname         │
│  5. Creates marker file (/var/lib/aap-firstboot-done)   │
│  6. AAP web UI available on port 443 (~30min)           │
└─────────────────────────────────────────────────────────┘
```

**Key specs:**
- **Deployment**: Containerized AAP 2.6 using rootless Podman
- **Topology**: Growth (all-in-one) — Controller, Hub, EDA, Gateway, PostgreSQL on single host
- **Instance type**: t3.2xlarge (8 vCPU, 32GB RAM) minimum
- **Disk**: 200GB GP3 (encrypted)
- **Build time**: ~60-90 minutes
- **First-boot reconfiguration**: ~30 minutes

## Prerequisites

1. [Packer](https://developer.hashicorp.com/packer/install) >= 1.9.0
2. [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/) >= 2.14
3. [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.6
4. AWS credentials configured (`aws configure` or environment variables)
5. **Red Hat Subscription** with AAP entitlement ([60-day free trial](https://developers.redhat.com/) available)
6. **AAP containerized bundle** uploaded to S3:
   ```
   s3://your-s3-bucket/aap/ansible-automation-platform-containerized-setup-bundle-2.6-5-x86_64.tar.gz
   ```
7. Required Ansible collections:
   ```bash
   ansible-galaxy collection install -r ansible/requirements.yml
   ```

## Quick Start

```bash
# 1. Build the AMI
cd packer/
packer init .
packer build \
  -var "rhsm_username=your-redhat-email@example.com" \
  -var "rhsm_password=your-redhat-password" \
  .

# 2. Deploy with Terraform
cd ../terraform/environments/dev/
# Update aap_ami_id in terraform.tfvars with the AMI ID from step 1
terraform init
terraform apply

# 3. Wait ~30 minutes for first-boot reconfiguration, then access:
# https://<public_dns>  (admin / changeme)
```

## Build the AMI

### Local Build

```bash
cd packer/

# Initialize Packer plugins
packer init .

# Validate the template
packer validate \
  -var "rhsm_username=your-redhat-email@example.com" \
  -var "rhsm_password=your-redhat-password" \
  .

# Build the AMI
packer build \
  -var "rhsm_username=your-redhat-email@example.com" \
  -var "rhsm_password=your-redhat-password" \
  -var "aap_admin_password=YourSecurePassword123" \
  .
```

### Build Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `rhsm_username` | *(required)* | Red Hat account email |
| `rhsm_password` | *(required)* | Red Hat account password |
| `aap_admin_password` | `changeme` | AAP admin UI password |
| `aws_region` | `us-east-1` | AWS region to build in |
| `instance_type` | `t3.2xlarge` | Builder instance type |
| `volume_size` | `200` | Root volume size (GB) |
| `vpc_id` | *(default VPC)* | VPC for the builder instance |
| `subnet_id` | *(auto-selected)* | Subnet for the builder instance |

### Build Output

The AMI ID is saved to `packer-manifest.json`:
```bash
jq -r '.builds[-1].artifact_id | split(":")[1]' packer-manifest.json
```

## Deploy with Terraform

### Configure

Edit `terraform/environments/dev/terraform.tfvars`:
```hcl
# AAP EC2 Instance - Pre-baked AMI from Packer build
aap_ami_id   = "ami-XXXXXXXXXXXX"  # AMI ID from Packer build
aap_key_name = "your-ssh-key"       # Existing EC2 key pair name
```

### Apply

```bash
cd terraform/environments/dev/

terraform init
terraform plan
terraform apply

# Or target just the EC2 module:
terraform apply -target="module.ec2_aap"
```

### Terraform Outputs

| Output | Description |
|--------|-------------|
| `aap_instance_id` | EC2 instance ID |
| `aap_public_ip` | Public IP address |
| `aap_controller_url` | Controller web UI URL |
| `aap_hub_url` | Private Automation Hub URL |
| `aap_ssh_command` | SSH command to connect |

## First-Boot Reconfiguration

The AMI includes an `aap-firstboot` systemd service that automatically handles the hostname/TLS problem inherent to prebaked AAP images.

### Why It's Needed

During the Packer build, AAP generates TLS certificates and database entries bound to the **build-time hostname** (e.g., `ip-172-31-19-38.ec2.internal`). When the AMI launches on a new instance with a different hostname, the gateway proxy can't load listener configs due to the TLS certificate mismatch.

### How It Works

1. **On boot**, `aap-firstboot.service` starts automatically
2. **Compares** the current hostname with the saved build-time hostname
3. **If different** (always on first launch from AMI):
   - Stops all AAP systemd user services
   - Removes all Podman containers and volumes
   - Removes old TLS certificates and AAP data
   - Generates a new installer inventory with the correct hostname
   - Runs the AAP installer (fresh install, ~30 minutes)
   - Cleans up the inventory file (contains passwords)
   - Creates marker file `/var/lib/aap-firstboot-done`
4. **If same hostname** (e.g., instance reboot): Skips reconfiguration
5. **Subsequent boots**: Service doesn't start (marker file exists)

### Monitoring First-Boot Progress

```bash
# Watch the firstboot service log
sudo journalctl -u aap-firstboot -f

# Or read the log file
sudo tail -f /var/log/aap-firstboot.log

# Check service status
sudo systemctl status aap-firstboot
```

### Key Files on the Instance

| File | Purpose |
|------|---------|
| `/usr/local/bin/aap-firstboot.sh` | Reconfiguration script |
| `/etc/systemd/system/aap-firstboot.service` | Systemd service unit |
| `/var/lib/aap-build-hostname` | Build-time hostname (for comparison) |
| `/var/lib/aap-firstboot-done` | Marker file (prevents re-runs) |
| `/var/log/aap-firstboot.log` | Detailed log output |

## AAP Access

After first-boot reconfiguration completes (~30 minutes after launch):

| Service | URL | Port |
|---------|-----|------|
| Controller (Gateway) | `https://<public_dns>` | 443 |
| Private Automation Hub | `https://<public_dns>:8443` | 8443 |
| Event-Driven Ansible | `https://<public_dns>:8444` | 8444 |

**Default credentials:**
- Username: `admin`
- Password: `changeme` (or as set via `aap_admin_password` during build)

> **Important**: Change the admin password immediately after first login.

### Security Group Ports

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Allowed CIDRs | SSH access |
| 443 | TCP | Allowed CIDRs | AAP Controller / Gateway |
| 8443 | TCP | Allowed CIDRs | Private Automation Hub |
| 27199 | TCP | VPC CIDR only | Receptor mesh |
| 5432 | TCP | VPC CIDR only | PostgreSQL |

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/packer-aap.yml`) automates the build:

### Triggers

- **Push to `main`**: Changes in `packer/**` or `.github/workflows/packer-aap.yml`
- **Pull request**: Validation only (no build)
- **Manual**: `workflow_dispatch` from GitHub Actions UI

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | IAM role ARN for GitHub Actions OIDC |
| `RHSM_USERNAME` | Red Hat account email |
| `RHSM_PASSWORD` | Red Hat account password |
| `AAP_ADMIN_PASSWORD` | *(Optional)* Custom admin password |

### IAM Role Configuration

The GitHub Actions IAM role (created by the Terraform IAM module) must have:
- **Maximum session duration**: 2 hours (7200 seconds) — the build takes ~90 minutes
- **OIDC trust policy** for `token.actions.githubusercontent.com`
- **Permissions**: EC2, S3 (read from bundle bucket), IAM (temp instance profile)

## Multi-Platform Support

The firstboot reconfiguration is **platform-agnostic** — it uses only standard Linux commands (`hostname`, `hostnamectl`, `su`) with no cloud-specific APIs.

| Platform | Hostname Source | Status |
|----------|----------------|--------|
| AWS EC2 | cloud-init / DHCP metadata | Fully tested |
| vCenter / VMware | open-vm-tools / guest customization | Dedicated build — see `packer-vsphere/` |
| Bare metal | DHCP / manual config | Compatible |
| Other clouds | cloud-init / DHCP | Compatible |

### vCenter / VMware Deployment

A dedicated vSphere build is available in the `packer-vsphere/` directory. It uses the `vsphere-iso` Packer builder with a RHEL 9 kickstart and the same Ansible roles to produce a VM template directly on vCenter — no AMI export needed. See [`packer-vsphere/README.md`](../packer-vsphere/README.md) for full details.

## Troubleshooting

### First-boot service didn't start automatically

**Cause**: Systemd ordering cycle — older AMIs have `After=cloud-final.service` which conflicts with `WantedBy=multi-user.target`. Fixed in latest Ansible roles (`After=cloud-init.service`).
**Fix**: The Terraform EC2 module user_data automatically patches the service file and starts it for older AMIs. If running manually:
```bash
sudo sed -i 's/cloud-final.service/cloud-init.service/' /etc/systemd/system/aap-firstboot.service
sudo systemctl daemon-reload
sudo systemctl start aap-firstboot
sudo journalctl -u aap-firstboot -f
```

### SSL certificate errors during first-boot reinstall

**Cause**: Old TLS certs persisting in Podman volumes (not just the host directory). Fixed in the latest firstboot script and Terraform user_data pre-cleanup.
**Fix**: If using an older AMI without the fix, run a full manual cleanup, then restart:
```bash
# As ec2-user
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user stop 'automation-*' 'receptor*' 'redis*' 'postgresql*' 2>/dev/null; true
podman stop -a -t 10; true
podman rm -a -f; true
podman volume rm -a -f; true
rm -rf ~/aap

# Then as root
sudo systemctl start aap-firstboot
```

### Packer build times out waiting for AMI

**Cause**: 200GB EBS snapshot takes 30+ minutes; Packer's default wait is too short.
**Fix**: Add `aws_polling` to `aap-rhel9.pkr.hcl`:
```hcl
aws_polling {
  delay_seconds = 30
  max_attempts  = 120
}
```
**Note**: The AMI is usually created successfully even if Packer reports a timeout. Check the AWS Console under EC2 > AMIs.

### AWS credentials expire during Packer build

**Cause**: Default OIDC session is 1 hour; build takes ~90 minutes.
**Fix**: Ensure the GitHub Actions workflow has `role-duration-seconds: 7200` and the IAM role's max session duration is set to 2 hours.

### Web UI not accessible after first-boot completes

Check in order:
1. **Security group**: Ensure your IP is in `aap_allowed_cidrs`
2. **Firstboot status**: `sudo systemctl status aap-firstboot` (should show `active (exited)`)
3. **Containers running**: `podman ps` (as ec2-user, should show ~22 containers)
4. **Port listening**: `ss -tlnp | grep 443`
5. **Firewall**: `sudo firewall-cmd --list-ports`

### Container issues

**Important**: Never use `podman restart --all` for AAP containers. They are managed by systemd user services. Instead:
```bash
# Check container status
podman ps -a

# Restart a specific service
systemctl --user restart automation-controller-web

# View service logs
journalctl --user -u automation-controller-web -f
```

## Security Notes

- RHSM credentials are used only during the Packer build and removed from the final AMI
- SSH host keys are removed from the AMI and regenerated on first boot
- The AAP installer inventory (containing passwords) is deleted after installation
- The firstboot script (contains embedded passwords) is owned by root with mode `0700`
- All RHSM registration data, logs, shell histories, and temp files are cleaned from the AMI
- The firstboot inventory is generated at runtime and deleted after the installer completes
- **Change the admin password immediately after first login**

## Project Structure

```
packer/
├── aap-rhel9.pkr.hcl              # Packer template (amazon-ebs builder)
├── variables.pkr.hcl              # Packer variable definitions
├── packer-manifest.json           # Build output (AMI ID)
├── README.md                      # This file
└── ansible/
    ├── playbook.yml                # Main playbook (orchestrates all roles)
    ├── requirements.yml            # Ansible Galaxy collections
    └── roles/
        ├── rhsm/                   # Red Hat Subscription Manager registration
        │   └── tasks/main.yml
        ├── aap-prereqs/            # Install Podman, ansible-core, dependencies
        │   └── tasks/main.yml
        ├── aap-install/            # Extract bundle, run AAP installer
        │   ├── defaults/main.yml   # Default passwords and paths
        │   ├── tasks/main.yml      # Installation tasks
        │   └── templates/
        │       └── inventory.j2    # AAP installer inventory template
        ├── aap-firstboot/          # First-boot hostname reconfiguration
        │   ├── defaults/main.yml   # Marker file paths, credentials
        │   ├── tasks/main.yml      # Install script and systemd service
        │   └── templates/
        │       ├── aap-firstboot.sh.j2       # Reconfiguration script
        │       └── aap-firstboot.service.j2  # Systemd oneshot service
        └── cleanup/                # Remove secrets, logs, SSH keys from AMI
            └── tasks/main.yml
```

## Getting a Red Hat Subscription

If you don't have a Red Hat subscription:

1. Visit [Red Hat Developers](https://developers.redhat.com/)
2. Create a free account
3. Subscribe to the [60-day Ansible Automation Platform trial](https://www.redhat.com/en/technologies/management/ansible/trial)
4. Use your Red Hat account credentials for `rhsm_username` and `rhsm_password`
5. Note: Simple Content Access (SCA) is enabled by default on trial subscriptions
