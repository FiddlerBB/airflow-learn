# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Get default subnet
data "aws_subnet" "default" {
  vpc_id            = data.aws_vpc.default.id
  availability_zone = "${var.aws_region}a"
  default_for_az    = true
}

# Security group for EC2
resource "aws_security_group" "ec2_sg" {
  name_prefix = "ec2-sg-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "main" {
  ami           = "ami-0ec18f6103c5e0491" # Amazon Linux 2023
  instance_type = "t3.medium"
  key_name      = "mlops_keypair"

  subnet_id                   = data.aws_subnet.default.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true
  root_block_device {
    volume_size           = 10    # Size in GB
    volume_type           = "gp2" # General Purpose SSD
    delete_on_termination = true
    tags = {
      Name = "mlops-root-volume"
    }
  }
  tags = {
    Name = "airflow-ec2"
  }
}

# Output the public IP
output "ec2_public_ip" {
  value = aws_instance.main.public_ip
}
