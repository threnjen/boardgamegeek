# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "zone-type"
    values = ["availability-zone"]
  }
}
# resource "aws_eip" "nat-gateway" {
#   domain   = "vpc"
# }
# resource "aws_nat_gateway" "example" {
#   allocation_id = aws_eip.nat-gateway.id
#   subnet_id     = module.vpc.private_subnets[0]

#   tags = {
#     Name = var.t2v-transformers
#   }

# }
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "meeplemasters"

  cidr = var.vpc_cidr_block

  azs             = data.aws_availability_zones.available.names
  private_subnets = slice(var.private_subnet_cidr_blocks, 0, var.private_subnet_count)
  public_subnets  = slice(var.public_subnet_cidr_blocks, 0, var.public_subnet_count)

  map_public_ip_on_launch = false
}

resource "aws_security_group" "shared_resources_sg" {
  name        = "shared_resources_sg"
  description = "Allows access amongst AWS services when attached to resources"
  vpc_id      = module.vpc.vpc_id
  egress = [
    {
      "cidr_blocks" : [
        "0.0.0.0/0"
      ],
      "description" : "",
      "from_port" : 0,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "-1",
      "security_groups" : [],
      "self" : false,
      "to_port" : 0
    }
  ]
  tags = {
    Name = "shared_resources_sg"
  }
}

resource "aws_security_group" "ec2_dagster_port_access" {
  name        = "ec2_dagster_port_access"
  description = "Allows access to port 3000 on EC2 from specific IP range"
  vpc_id      = module.vpc.vpc_id
  egress = [
    {
      "cidr_blocks" : [
        "0.0.0.0/0"
      ],
      "description" : "",
      "from_port" : 0,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "-1",
      "security_groups" : [],
      "self" : false,
      "to_port" : 0
    }
  ]
  ingress = [
    {
      "cidr_blocks" : [
        "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
      ],
      "description" : "",
      "from_port" : 3000,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 3000
    }
  ]
  tags = {
    Name = "ec2_dagster_port_access"
  }
}

resource "aws_security_group" "ec2_weaviate_port_access" {
  name        = "ec2_weaviate_port_access"
  description = "Allows access to port 8080 on EC2 from specific IP range"
  vpc_id      = module.vpc.vpc_id
  egress = [
    {
      "cidr_blocks" : [
        "0.0.0.0/0"
      ],
      "description" : "",
      "from_port" : 0,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "-1",
      "security_groups" : [],
      "self" : false,
      "to_port" : 0
    }
  ]
  ingress = [
    {
      "cidr_blocks" : [
        "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
      ],
      "description" : "",
      "from_port" : 8080,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 8080
    },
    {
      "cidr_blocks" : [
        "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
      ],
      "description" : "",
      "from_port" : 50051,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 50051
    },
    {
      "cidr_blocks" : [
        "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
      ],
      "description" : "",
      "from_port" : 80,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 80
    },
    {
      "cidr_blocks" : [var.vpc_cidr_block
      ],
      "description" : "",
      "from_port" : 8080,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 8080
    },
    {
      "cidr_blocks" : [var.vpc_cidr_block
      ],
      "description" : "",
      "from_port" : 80,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 80
    },
    {
      "cidr_blocks" : [var.vpc_cidr_block
      ],
      "description" : "",
      "from_port" : 50051,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 50051
    },
    {
      "cidr_blocks" : [],
      "description" : "",
      from_port = 8080
      to_port   = 8080
      protocol  = "tcp"
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "self" : false,
      security_groups = [aws_security_group.shared_resources_sg.id]
    },
  ]
  tags = {
    Name = "ec2_weaviate_port_access"
  }
}

resource "aws_security_group" "ec2_ssh_access" {
  name        = "ec2_ssh_access"
  description = "Allows SSH access to EC2 for authorized IPs"
  vpc_id      = module.vpc.vpc_id
  egress = [
    {
      "cidr_blocks" : [
        "0.0.0.0/0"
      ],
      "description" : "",
      "from_port" : 0,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "-1",
      "security_groups" : [],
      "self" : false,
      "to_port" : 0
    }
  ]
  ingress = [
    {
      "cidr_blocks" : [
        "${var.MY_IP_FIRST_THREE_BLOCKS}.0/24"
      ],
      "description" : "",
      "from_port" : 22,
      "ipv6_cidr_blocks" : [],
      "prefix_list_ids" : [],
      "protocol" : "tcp",
      "security_groups" : [],
      "self" : false,
      "to_port" : 22
    }
  ]
  tags = {
    Name = "ec2_ssh_access"
  }
}
