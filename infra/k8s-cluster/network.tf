resource "yandex_vpc_network" "k8s" {
  name = var.network_name
}

resource "yandex_vpc_subnet" "k8s" {
  name           = "${var.cluster_name}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.k8s.id
  v4_cidr_blocks = [var.subnet_cidr]
}

resource "yandex_vpc_security_group" "k8s_main" {
  name        = "${var.cluster_name}-main-sg"
  description = "Rules required for the Managed K8s cluster (master + nodes)."
  network_id  = yandex_vpc_network.k8s.id

  ingress {
    description       = "Allow pods to talk to each other inside the cluster"
    protocol          = "ANY"
    predefined_target = "self_security_group"
    from_port         = 0
    to_port           = 65535
  }

  ingress {
    description    = "Cluster service network"
    protocol       = "ANY"
    v4_cidr_blocks = ["10.96.0.0/16"]
    from_port      = 0
    to_port        = 65535
  }

  ingress {
    description    = "Cluster pod network"
    protocol       = "ANY"
    v4_cidr_blocks = ["10.112.0.0/16"]
    from_port      = 0
    to_port        = 65535
  }

  ingress {
    description    = "ICMP from anywhere (debug)"
    protocol       = "ICMP"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Yandex LB healthcheck"
    protocol       = "TCP"
    v4_cidr_blocks = ["198.18.235.0/24", "198.18.248.0/24"]
    from_port      = 0
    to_port        = 65535
  }

  ingress {
    description    = "NodePort range from anywhere (will be tightened later by Ingress)"
    protocol       = "TCP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 30000
    to_port        = 32767
  }

  egress {
    description    = "Outbound to anywhere (pull images, talk to API, etc.)"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}
