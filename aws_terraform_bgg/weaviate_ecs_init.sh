sudo yum update -y  # For Amazon Linux 2
sudo yum install -y docker
sudo service docker start
sudo yum install -y git
sudo usermod -aG docker ec2-user  # Replace `ec2-user` with your username if different
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose 