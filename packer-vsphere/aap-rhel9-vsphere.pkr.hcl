# =============================================================================
# AAP 2.6 Containerized - vSphere/vCenter Image Build
# =============================================================================
# Builds a VM template on vCenter with Red Hat Ansible Automation Platform 2.6
# (Containerized) pre-installed. On first boot from the template, a systemd
# service automatically reconfigures AAP for the new hostname and regenerates
# TLS certificates.
#
# Prerequisites:
#   1. RHEL 9 ISO uploaded to a vCenter datastore
#   2. AAP containerized setup bundle downloaded locally
#   3. RHSM credentials for registry.redhat.io authentication
#
# Usage:
#   cd packer-vsphere/
#   packer init -upgrade .
#   packer validate -var-file=vsphere.auto.pkrvars.hcl .
#   packer build -var-file=vsphere.auto.pkrvars.hcl .
# =============================================================================

packer {
  required_plugins {
    vsphere = {
      version = ">= 1.4.0"
      source  = "github.com/hashicorp/vsphere"
    }
    ansible = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

locals {
  timestamp     = formatdate("YYYYMMDD-hhmmss", timestamp())
  template_name = "${var.vm_name_prefix}-${local.timestamp}"
  ansible_dir   = "${path.root}/ansible"
}

# =============================================================================
# vSphere ISO Builder
# =============================================================================
source "vsphere-iso" "rhel9-aap" {
  # --- vCenter Connection ---
  vcenter_server      = var.vcenter_server
  username            = var.vcenter_username
  password            = var.vcenter_password
  insecure_connection = var.vcenter_insecure
  datacenter          = var.vcenter_datacenter
  cluster             = var.vcenter_cluster
  datastore           = var.vcenter_datastore
  folder              = var.vcenter_folder

  # --- VM Configuration ---
  vm_name         = local.template_name
  guest_os_type   = "rhel9_64Guest"
  CPUs            = var.vm_cpus
  RAM             = var.vm_ram_mb
  RAM_reserve_all = true
  firmware        = "efi"

  storage {
    disk_size             = var.vm_disk_size_mb
    disk_thin_provisioned = true
  }

  network_adapters {
    network      = var.vcenter_network
    network_card = "vmxnet3"
  }

  # --- RHEL 9 ISO ---
  iso_paths = var.iso_paths

  # Kickstart via HTTP server (Packer serves files from http/ directory)
  http_directory = "${path.root}/http"
  boot_wait      = "5s"
  boot_command = [
    "<up>",
    "e",
    "<down><down><end>",
    " inst.text inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/ks-rhel9.cfg",
    "<leftCtrlOn>x<leftCtrlOff>"
  ]

  # --- SSH Connection ---
  ssh_username = var.ssh_username
  ssh_password = var.ssh_password
  ssh_timeout  = "30m"

  # --- Template Settings ---
  convert_to_template = true
  notes               = "AAP 2.6 Containerized (Controller + Hub + EDA) - Built ${local.timestamp}"
}

# =============================================================================
# Build Pipeline
# =============================================================================
build {
  name    = "aap-rhel9-vsphere"
  sources = ["source.vsphere-iso.rhel9-aap"]

  # Wait for OS to settle after kickstart
  provisioner "shell" {
    inline = [
      "echo 'Waiting for system to settle...'",
      "sleep 10",
      "echo 'System ready for provisioning.'"
    ]
  }

  # Upload AAP bundle from the build machine
  provisioner "file" {
    source      = var.aap_bundle_local_path
    destination = "/tmp/aap-bundle.tar.gz"
  }

  # Install required Ansible collections
  provisioner "shell-local" {
    inline = [
      "ansible-galaxy collection install -r ${local.ansible_dir}/requirements.yml --force"
    ]
  }

  # Run Ansible playbook for full AAP installation
  provisioner "ansible" {
    playbook_file = "${local.ansible_dir}/playbook.yml"
    user          = var.ssh_username

    extra_arguments = [
      "--extra-vars", "rhsm_username=${var.rhsm_username}",
      "--extra-vars", "rhsm_password=${var.rhsm_password}",
      "--extra-vars", "aap_admin_password=${var.aap_admin_password}",
      "--extra-vars", "aap_install_user=${var.ssh_username}",
      "--scp-extra-args", "'-O'",
      "-v"
    ]

    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SSH_ARGS=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    ]
  }

  # Final cleanup - remove credentials, logs, and machine-specific data
  provisioner "shell" {
    inline = [
      "echo 'Final template preparation...'",
      "sudo rm -rf /tmp/* /var/tmp/*",
      "sudo rm -f /root/.bash_history",
      "sudo rm -f /home/${var.ssh_username}/.bash_history",
      "sudo rm -rf /var/log/journal/*",
      "sudo truncate -s 0 /var/log/messages /var/log/secure /var/log/audit/audit.log || true",
      # Remove machine-id so each clone gets a unique one
      "sudo truncate -s 0 /etc/machine-id",
      "sudo rm -f /var/lib/dbus/machine-id",
      # Clean SSH host keys so each clone regenerates them
      "sudo rm -f /etc/ssh/ssh_host_*",
      "echo 'Template preparation complete.'"
    ]
  }

  post-processor "manifest" {
    output     = "packer-manifest-vsphere.json"
    strip_path = true
  }
}
