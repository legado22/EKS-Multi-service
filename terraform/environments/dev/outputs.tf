# AAP EC2 Instance Outputs
output "aap_instance_id" {
  description = "AAP EC2 instance ID"
  value       = module.ec2_aap.instance_id
}

output "aap_public_ip" {
  description = "AAP EC2 public IP address"
  value       = module.ec2_aap.public_ip
}

output "aap_controller_url" {
  description = "AAP Controller web UI URL"
  value       = module.ec2_aap.aap_controller_url
}

output "aap_hub_url" {
  description = "AAP Private Automation Hub URL"
  value       = module.ec2_aap.aap_hub_url
}

output "aap_ssh_command" {
  description = "SSH command to connect to AAP instance"
  value       = "ssh ec2-user@${module.ec2_aap.public_ip}"
}
