output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

output "instance_arn" {
  description = "ARN of the EC2 instance"
  value       = aws_instance.main.arn
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.main.public_ip
}

output "private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.main.private_ip
}

output "public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.main.public_dns
}

output "private_dns" {
  description = "Private DNS name of the EC2 instance"
  value       = aws_instance.main.private_dns
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.ec2.id
}

output "ami_id" {
  description = "AMI ID used for the instance"
  value       = local.ami_id
}

output "ssh_connection_command" {
  description = "SSH connection command"
  value       = "ssh ${var.ssh_username}@${aws_instance.main.public_ip}"
}

output "aap_controller_url" {
  description = "AAP Controller web UI URL"
  value       = var.enable_aap_ports ? "https://${aws_instance.main.public_dns}" : null
}

output "aap_hub_url" {
  description = "AAP Private Automation Hub URL"
  value       = var.enable_aap_ports ? "https://${aws_instance.main.public_dns}:8443" : null
}

output "aap_eda_url" {
  description = "AAP Event-Driven Ansible URL"
  value       = var.enable_aap_ports ? "https://${aws_instance.main.public_dns}:8444" : null
}
