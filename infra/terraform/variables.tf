variable "cloud_id" {
  description = "Yandex Cloud Cloud ID."
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID (where resources will be created)."
  type        = string
}

variable "zone" {
  description = "Availability zone (e.g. ru-central1-d)."
  type        = string
  default     = "ru-central1-d"
}

variable "vm_name" {
  description = "Name of the VM resource."
  type        = string
  default     = "url-shortener"
}

variable "vm_cores" {
  description = "Number of vCPUs."
  type        = number
  default     = 2
}

variable "vm_memory_gb" {
  description = "RAM in GB."
  type        = number
  default     = 2
}

variable "vm_core_fraction" {
  description = "Guaranteed share of vCPU per core (5/20/50/100). 100 = full, 20 = burstable."
  type        = number
  default     = 100
}

variable "vm_disk_gb" {
  description = "Boot disk size in GB."
  type        = number
  default     = 20
}

variable "vm_image_family" {
  description = "Image family for the boot disk (Ubuntu LTS)."
  type        = string
  default     = "ubuntu-2404-lts"
}

variable "vm_user" {
  description = "Username created on the VM (must match SSH key, see ssh_public_key)."
  type        = string
  default     = "ulya"
}

variable "ssh_public_key" {
  description = "SSH public key (single line, content of ~/.ssh/*.pub) for vm_user."
  type        = string
}

variable "network_name" {
  description = "Name of the VPC network."
  type        = string
  default     = "url-shortener-net"
}

variable "subnet_name" {
  description = "Name of the subnet."
  type        = string
  default     = "url-shortener-subnet"
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet."
  type        = string
  default     = "10.130.0.0/24"
}
