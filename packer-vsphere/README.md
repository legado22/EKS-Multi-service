# AAP 2.6 Containerized - vSphere/vCenter Build

Builds a **VM template** on vCenter with Red Hat Ansible Automation Platform 2.6 (Containerized) pre-installed. When a VM is cloned from this template, a systemd firstboot service automatically detects the new hostname and reconfigures AAP with fresh TLS certificates — no manual intervention required.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Packer Build Flow                      │
│                                                          │
│  RHEL 9 ISO → Kickstart → Ansible Provisioning → Template│
│                                                          │
│  Ansible Roles:                                          │
│  ├── rhsm          → RHEL subscription + registry auth   │
│  ├── aap-prereqs   → Podman, dependencies, bundle extract│
│  ├── aap-install   → Run AAP containerized installer     │
│  ├── aap-firstboot → Systemd service for hostname reconf │
│  └── cleanup       → Remove credentials from template    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  Deployment Flow                          │
│                                                          │
│  Clone Template → VMware Guest Customization → Boot       │
│       │                                                   │
│       └→ aap-firstboot.service detects hostname change    │
│          └→ Full cleanup (containers, volumes, data)      │
│             └→ Re-runs AAP installer with new hostname    │
│                └→ Fresh TLS certs → AAP ready (~35 min)   │
└──────────────────────────────────────────────────────────┘
```

## AAP Components

The template includes the full AAP Growth topology (all-in-one):

| Component | Port | Description |
|---|---|---|
| **Automation Gateway** | 443 | Unified entry point and SSO |
| **Automation Controller** | — | Job execution engine |
| **Automation Hub** | 8443 | Content management and collections |
| **Event-Driven Ansible** | — | Event-driven automation |
| **PostgreSQL** | 5432 | Shared database |
| **Redis** | — | Cache and message broker |

All components run as **rootless Podman containers** managed by systemd user services.

## Prerequisites

| Requirement | Detail |
|---|---|
| **vCenter** | 7.x or 8.x with permissions to create VMs and templates |
| **ESXi Host** | 8 vCPU, 32GB RAM, 200GB storage available for the build VM |
| **RHEL 9 ISO** | Uploaded to a vCenter datastore |
| **AAP Bundle** | `ansible-automation-platform-containerized-setup-bundle-2.6-*.tar.gz` |
| **RHSM Account** | Red Hat subscription with SCA enabled for `registry.redhat.io` |
| **Network** | DHCP during build; outbound to `registry.redhat.io` for container images |
| **Packer** | >= 1.9.0 installed on the build machine |
| **Ansible** | `ansible-core >= 2.17, < 2.18` on the build machine |

## Quick Start

```bash
# 1. Navigate to this directory
cd packer-vsphere/

# 2. Copy and edit the variables file
cp vsphere.auto.pkrvars.hcl.example vsphere.auto.pkrvars.hcl
# Edit vsphere.auto.pkrvars.hcl with your vCenter details

# 3. Update the kickstart password to match your pkrvars
# Edit http/ks-rhel9.cfg → change CHANGE_ME_IN_PKRVARS to match ssh_password

# 4. Initialize Packer plugins
packer init -upgrade .

# 5. Validate
packer validate -var-file=vsphere.auto.pkrvars.hcl .

# 6. Build
packer build -var-file=vsphere.auto.pkrvars.hcl .
```

## Deploying from the Template

### Via vCenter UI

1. Right-click the template → **New VM from This Template**
2. Configure: name, folder, cluster, datastore, network
3. In **Customize guest OS**: set hostname and network (static IP or DHCP)
4. Power on the VM
5. Wait ~35 minutes for the firstboot service to reconfigure AAP
6. Access AAP at `https://<vm-hostname>` (admin / changeme)

### Via Terraform (vsphere provider)

```hcl
resource "vsphere_virtual_machine" "aap" {
  name             = "aap-production"
  resource_pool_id = data.vsphere_compute_cluster.cluster.resource_pool_id
  datastore_id     = data.vsphere_datastore.ds.id
  guest_id         = "rhel9_64Guest"
  num_cpus         = 8
  memory           = 32768

  clone {
    template_uuid = data.vsphere_virtual_machine.aap_template.id
    customize {
      linux_options {
        host_name = "aap-production"
        domain    = "example.com"
      }
      network_interface {
        ipv4_address = "10.0.1.50"
        ipv4_netmask = 24
      }
      ipv4_gateway = "10.0.1.1"
    }
  }
}
```

## How the Firstboot Service Works

1. **During Packer build**: AAP is fully installed and the build-time hostname is saved to `/var/lib/aap-build-hostname`
2. **On first boot of a clone**: The `aap-firstboot.service` (systemd oneshot) compares the current hostname against the saved build-time hostname
3. **If hostname changed**: The service performs a full reset — stops all AAP Podman containers, removes volumes (which contain old TLS certs), removes the AAP data directory, then re-runs the AAP installer with a fresh inventory using the new hostname
4. **Result**: Fresh TLS certificates are generated for the new hostname, all AAP services start cleanly
5. **Marker file**: After successful reconfiguration, `/var/lib/aap-firstboot-done` is created to prevent re-running on subsequent reboots

## Monitoring the Firstboot

After cloning and powering on a VM:

```bash
# Watch firstboot progress in real-time
sudo journalctl -u aap-firstboot -f

# Check firstboot service status
sudo systemctl status aap-firstboot

# View the full firstboot log
sudo cat /var/log/aap-firstboot.log
```

## File Structure

```
packer-vsphere/
├── aap-rhel9-vsphere.pkr.hcl          # Main Packer build config
├── variables.pkr.hcl                   # Variable definitions
├── vsphere.auto.pkrvars.hcl.example    # Example values (copy and edit)
├── ansible/                            # Ansible playbook and roles
│   ├── playbook.yml
│   ├── requirements.yml
│   └── roles/
│       ├── rhsm/                       # RHEL subscription management
│       ├── aap-prereqs/                # Podman, dependencies, bundle extraction
│       ├── aap-install/                # AAP containerized installer
│       ├── aap-firstboot/              # Systemd firstboot reconfiguration
│       └── cleanup/                    # Credential removal from template
├── http/
│   └── ks-rhel9.cfg                    # RHEL 9 kickstart for automated OS install
└── README.md
```

## Security Notes

- **Credentials file** (`vsphere.auto.pkrvars.hcl`) contains sensitive values — never commit to version control
- **RHSM credentials** are removed from the template during the Ansible cleanup role
- **SSH password** should be rotated or disabled after the build (use SSH keys in production)
- **SELinux** is set to enforcing mode in the kickstart
- **machine-id** is cleared so each clone gets a unique identity
- **SSH host keys** are removed so each clone regenerates its own

## Troubleshooting

| Issue | Solution |
|---|---|
| Kickstart not found during boot | Verify the build machine firewall allows the Packer HTTP server port |
| SSH timeout after kickstart | Check vCenter network has DHCP or update kickstart with a static IP |
| ansible-core Galaxy API errors | Pin to `ansible-core>=2.17,<2.18` (2.20.x has a known regression) |
| Firstboot ordering cycle | Ensure the service file has `After=cloud-init.service` (not `cloud-final.service`) |
| SSL cert errors after clone | Verify firstboot ran successfully — check `/var/log/aap-firstboot.log` |
| Template won't clone | Ensure `convert_to_template = true` is set in the Packer config |
