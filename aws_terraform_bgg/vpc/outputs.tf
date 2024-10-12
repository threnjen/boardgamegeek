output "vpc_id" {
  description = "ID of created VPC"
  value       = module.vpc.vpc_id
}

output "sg_ec2_dagster_port_access" {
  description = "SG id of ec2_dagster_port_access"
  value       = aws_security_group.ec2_dagster_port_access.id
}

output "sg_ec2_ssh_access" {
  description = "SG id of ec2_ssh_access"
  value       = aws_security_group.ec2_ssh_access.id
}

