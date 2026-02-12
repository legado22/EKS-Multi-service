# =============================================================================
# vSphere/vCenter Variables for AAP Image Build
# =============================================================================
# Copy vsphere.auto.pkrvars.hcl.example to vsphere.auto.pkrvars.hcl
# and fill in your vCenter-specific values before running the build.
# =============================================================================

# --- vCenter Connection ---
variable "vcenter_server" {
  type        = string
  description = "vCenter Server FQDN or IP address"
}

variable "vcenter_username" {
  type        = string
  description = "vCenter username (e.g., administrator@vsphere.local)"
}

variable "vcenter_password" {
  type        = string
  sensitive   = true
  description = "vCenter password"
}

variable "vcenter_insecure" {
  type        = bool
  default     = false
  description = "Allow insecure connection to vCenter (skip TLS verification)"
}

variable "vcenter_datacenter" {
  type        = string
  description = "vCenter datacenter name"
}

variable "vcenter_cluster" {
  type        = string
  description = "vCenter cluster name for the build VM"
}

variable "vcenter_datastore" {
  type        = string
  description = "vCenter datastore for the build VM and template"
}

variable "vcenter_folder" {
  type        = string
  default     = "Templates/AAP"
  description = "vCenter folder to store the VM template"
}

variable "vcenter_network" {
  type        = string
  description = "vCenter network/port group for the build VM (needs DHCP or static via kickstart)"
}

# --- ISO Configuration ---
variable "iso_paths" {
  type        = list(string)
  description = "Datastore path(s) to RHEL 9 ISO (e.g., [\"[datastore1] ISO/rhel-9.4-x86_64-dvd.iso\"])"
}

# --- VM Hardware ---
variable "vm_cpus" {
  type        = number
  default     = 8
  description = "Number of CPUs for the VM (minimum 8 for full AAP stack)"
}

variable "vm_ram_mb" {
  type        = number
  default     = 32768
  description = "RAM in MB (minimum 32GB = 32768 for full AAP stack)"
}

variable "vm_disk_size_mb" {
  type        = number
  default     = 204800
  description = "Disk size in MB (200GB = 204800)"
}

variable "vm_name_prefix" {
  type        = string
  default     = "aap-rhel9-template"
  description = "Prefix for the VM template name"
}

# --- SSH / OS Credentials ---
variable "ssh_username" {
  type        = string
  default     = "aapuser"
  description = "SSH user created during kickstart (also runs AAP install as rootless Podman)"
}

variable "ssh_password" {
  type        = string
  sensitive   = true
  description = "SSH password for the build user (set in kickstart, removed from template)"
}

# --- Red Hat Subscription ---
variable "rhsm_username" {
  type        = string
  sensitive   = true
  description = "Red Hat Subscription Manager username"
}

variable "rhsm_password" {
  type        = string
  sensitive   = true
  description = "Red Hat Subscription Manager password"
}

# --- AAP Configuration ---
variable "aap_admin_password" {
  type        = string
  sensitive   = true
  default     = "changeme"
  description = "Initial admin password for AAP Controller (change on first login)"
}

variable "aap_bundle_local_path" {
  type        = string
  description = "Local filesystem path to the AAP containerized setup bundle (.tar.gz)"
}
