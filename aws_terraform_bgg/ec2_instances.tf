module "weaviate_ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"

  name = "weaviate"

  instance_type          = "t2.micro"
  key_name               = "oregon_key"
  monitoring             = true
  vpc_security_group_ids = [output.sg_ec2_ssh_access, output.sg_ec2_weaviate_port_access]
  subnet_id              = output.public_subnets[0]

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }

  user_data = data.cloudinit_config.weaviate_ec2_instance.rendered
}

data "cloudinit_config" "weaviate_ec2_instance" {
  part {
    content_type = "text/x-shellscript"
    content      = file("./weaviate_ecs_init.sh")
  }

  part {
    content_type = "text/cloud-config"
    content = yamlencode({
      write_files = [
        {
          encoding    = "b64"
          content     = filebase64("../Dockerfiles/docker_compose.yml")
          path        = "/home/ec2-user/docker_compose.yml"
          owner       = "ec2-user:ec2-user"
          permissions = "0755"
        },
      ]
    })
  }
}

output "ec2_instance_public_ip" {
  value = module.ec2_instance.this_ec2_instance.public_ip
}