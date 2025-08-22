variable "region" { type = string }
variable "project_name" { type = string, default = "netauto-mini" }
variable "vpc_cidr" { type = string, default = "10.10.0.0/16" }
variable "public_subnet_cidr" { type = string, default = "10.10.1.0/24" }
variable "instance_type" { type = string, default = "t3.micro" }
variable "key_name" { type = string }
