resource "aws_instance" "weaviate_ec2_instance" {

  instance_type               = "t3.small"
  ami                         = "ami-055e3d4f0bbeb5878"
  key_name                    = "weaviate-ec2"
  monitoring                  = true
  vpc_security_group_ids      = [aws_security_group.ec2_ssh_access.id, aws_security_group.ec2_weaviate_port_access.id, aws_security_group.shared_resources_sg.id]
  subnet_id                   = module.vpc.public_subnets[0]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.weaviate_ec2_instance_role.name

  root_block_device {
    volume_size = 30
    encrypted   = true
  }
  tags = {
    Name        = "weaviate_embedder"
    Terraform   = "true"
    Environment = "dev"
  }

  user_data = data.cloudinit_config.weaviate_ec2_instance.rendered
}

resource "aws_iam_instance_profile" "weaviate_ec2_instance_role" {
  name = "test_profile"
  role = aws_iam_role.weaviate_ec2_instance.name
}

resource "aws_iam_role_policy_attachment" "weaviate_ec2_ssm_policy_attach" {
  role       = aws_iam_role.weaviate_ec2_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_ssm_activation" "weaviate_ec2_instance" {
  name               = "ssm_activation"
  description        = "Activate Weaviate EC2 instance"
  iam_role           = aws_iam_role.weaviate_ec2_instance.id
  registration_limit = "5"
  depends_on         = [aws_iam_role_policy_attachment.weaviate_ec2_ssm_policy_attach]
}

data "cloudinit_config" "weaviate_ec2_instance" {
  part {
    content_type = "text/x-shellscript"
    content      = file("./weaviate_ecs_init.sh")
  }
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "ssm.amazonaws.com",
        "ec2.amazonaws.com"
      ]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "weaviate_ec2_instance" {
  name               = "weaviate_ec2_instance"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

module "ssm_default_host_management" {
  source = "github.com/plus3it/terraform-aws-tardigrade-ssm-default-host-management"
}