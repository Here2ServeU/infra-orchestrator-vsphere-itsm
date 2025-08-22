variable "project_name" { type = string, default = "netauto-mini" }
variable "vsphere_user"    { type = string }
variable "vsphere_password"{ type = string }
variable "vsphere_server"  { type = string }

variable "datacenter"   { type = string }
variable "cluster"      { type = string }
variable "datastore"    { type = string }
variable "network_name" { type = string }
variable "template_name"{ type = string } # VM template to clone

variable "vm_name"   { type = string, default = "netauto-web" }
variable "cpu"       { type = number, default = 2 }
variable "memory_mb" { type = number, default = 2048 }
