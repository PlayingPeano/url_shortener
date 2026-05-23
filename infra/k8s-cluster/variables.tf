variable "cloud_id" {
  description = "Yandex Cloud Cloud ID."
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID (where K8s + registry will live)."
  type        = string
}

variable "zone" {
  description = "Availability zone (zonal cluster lives in a single zone)."
  type        = string
  default     = "ru-central1-d"
}

variable "cluster_name" {
  description = "Name of the Managed Kubernetes cluster."
  type        = string
  default     = "url-shortener-k8s"
}

variable "k8s_version" {
  description = "Kubernetes version (must be supported by the STABLE release channel)."
  type        = string
  default     = "1.31"
}

variable "node_cores" {
  description = "vCPU cores per K8s node."
  type        = number
  default     = 2
}

variable "node_memory_gb" {
  description = "RAM per K8s node, GB."
  type        = number
  default     = 4
}

variable "node_disk_gb" {
  description = "Boot disk size per K8s node, GB."
  type        = number
  default     = 30
}

variable "node_count" {
  description = "Fixed number of nodes in the group."
  type        = number
  default     = 1
}

variable "network_name" {
  description = "Name of the dedicated K8s VPC network."
  type        = string
  default     = "url-shortener-k8s-net"
}

variable "subnet_cidr" {
  description = "CIDR for the subnet used by the cluster master and nodes."
  type        = string
  default     = "10.140.0.0/24"
}

variable "registry_name" {
  description = "Name of the Yandex Container Registry."
  type        = string
  default     = "url-shortener-registry"
}
