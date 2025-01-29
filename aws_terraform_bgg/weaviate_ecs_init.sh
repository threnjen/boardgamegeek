!/bin/bash
sudo yum update -y
sudo yum install -y git
sudo yum install -y docker
sudo service docker start
sudo usermod -aG docker ec2-user
sudo mkdir -p /usr/local/lib/docker/cli-plugins/
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
# sudo yum install -y amazon-ssm-agent
# sudo systemctl enable amazon-ssm-agent
# sudo systemctl start amazon-ssm-agent
# sudo systemctl status amazon-ssm-agent


