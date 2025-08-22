data "aws_ami" "al2023" {
  most_recent = true
  owners = ["amazon"]
  filter { name = "name" values = ["al2023-ami-*-x86_64"] }
}

resource "aws_vpc" "this" { cidr_block = var.vpc_cidr }
resource "aws_internet_gateway" "igw" { vpc_id = aws_vpc.this.id }
data "aws_availability_zones" "azs" {}

resource "aws_subnet" "public" {
  vpc_id = aws_vpc.this.id
  cidr_block = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone = data.aws_availability_zones.azs.names[0]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route { cidr_block = "0.0.0.0/0" gateway_id = aws_internet_gateway.igw.id }
}
resource "aws_route_table_association" "assoc" {
  subnet_id = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "web" {
  name = "${var.project_name}-web-sg"
  vpc_id = aws_vpc.this.id
  ingress { from_port=22 to_port=22 protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
  ingress { from_port=80 to_port=80 protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
  egress  { from_port=0  to_port=0  protocol="-1"  cidr_blocks=["0.0.0.0/0"] }
}

resource "aws_instance" "web" {
  ami = data.aws_ami.al2023.id
  instance_type = var.instance_type
  subnet_id = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  key_name = var.key_name
  associate_public_ip_address = true
}

output "public_ip" { value = aws_instance.web.public_ip }
output "instance_id" { value = aws_instance.web.id }
output "region" { value = var.region }
