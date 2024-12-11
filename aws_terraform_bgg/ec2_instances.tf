resource "aws_instance" "weaviate_ec2_instance" {

  instance_type               = "t2.micro"
  ami                         = "ami-055e3d4f0bbeb5878"
  key_name                    = "oregon_key"
  monitoring                  = true
  vpc_security_group_ids      = [aws_security_group.ec2_ssh_access.id, aws_security_group.ec2_weaviate_port_access.id]
  subnet_id                   = module.vpc.public_subnets[0]
  associate_public_ip_address = true

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


data "cloudinit_config" "weaviate_ec2_instance" {
  part {
    content_type = "text/x-shellscript"
    content      = file("./weaviate_ecs_init.sh")
  }
}
