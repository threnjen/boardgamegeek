# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

provider "aws" {
  region = var.REGION
}

data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "zone-type"
    values = ["availability-zone"]
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  name = "meeplemasters"

  cidr = var.vpc_cidr_block

  azs             = data.aws_availability_zones.available.names
  private_subnets = slice(var.private_subnet_cidr_blocks, 0, var.private_subnet_count)
  public_subnets  = slice(var.public_subnet_cidr_blocks, 0, var.public_subnet_count)

  map_public_ip_on_launch = false
}

resource "aws_security_group" "ec2_dagster_port_access" {
  name = "ec2_dagster_port_access"
  description = "Allows access to port 3000 on EC2 from specific IP range"
  vpc_id = module.vpc.vpc_id
  egress = [
              {
                "cidr_blocks": [
                  "0.0.0.0/0"
                ],
                "description": "",
                "from_port": 0,
                "ipv6_cidr_blocks": [],
                "prefix_list_ids": [],
                "protocol": "-1",
                "security_groups": [],
                "self": false,
                "to_port": 0
              }
            ]
    ingress=[
              {
                "cidr_blocks": [
                  "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
                ],
                "description": "",
                "from_port": 22,
                "ipv6_cidr_blocks": [],
                "prefix_list_ids": [],
                "protocol": "tcp",
                "security_groups": [],
                "self": false,
                "to_port": 3000
              }
            ]

}

resource "aws_security_group" "ec2_ssh_access" {
  name = "ec2_ssh_access"
  description = "Allows SSH access to EC2 for authorized IPs"
  vpc_id = module.vpc.vpc_id
  egress = [
              {
                "cidr_blocks": [
                  "0.0.0.0/0"
                ],
                "description": "",
                "from_port": 0,
                "ipv6_cidr_blocks": [],
                "prefix_list_ids": [],
                "protocol": "-1",
                "security_groups": [],
                "self": false,
                "to_port": 0
              }
            ]
    ingress=[
              {
                "cidr_blocks": [
                  "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
                ],
                "description": "",
                "from_port": 22,
                "ipv6_cidr_blocks": [],
                "prefix_list_ids": [],
                "protocol": "tcp",
                "security_groups": [],
                "self": false,
                "to_port": 22
              }
            ]
}
