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

output "sg_ec2_weaviate_port_access" {
  description = "SG id of ec2_weaviate_port_access"
  value       = aws_security_group.ec2_weaviate_port_access.id
}

output "shared_resources_sg" {
  description = "SG id of shared_resources_sg"
  value       = aws_security_group.shared_resources_sg.id
}

output "public_subnets" {
  description = "Public subnets in the VPC"
  value       = module.vpc.public_subnets
}

output "private_subnets" {
  description = "Private subnets in the VPC"
  value       = module.vpc.private_subnets
}
