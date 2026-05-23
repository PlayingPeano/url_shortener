resource "yandex_kubernetes_cluster" "this" {
  name        = var.cluster_name
  description = "Managed K8s cluster for URL shortener (zonal, basic master)."

  network_id = yandex_vpc_network.k8s.id

  master {
    version   = var.k8s_version
    public_ip = true

    zonal {
      zone      = var.zone
      subnet_id = yandex_vpc_subnet.k8s.id
    }

    security_group_ids = [yandex_vpc_security_group.k8s_main.id]

    maintenance_policy {
      auto_upgrade = true

      maintenance_window {
        start_time = "03:00"
        duration   = "3h"
      }
    }
  }

  service_account_id      = yandex_iam_service_account.cluster.id
  node_service_account_id = yandex_iam_service_account.nodes.id

  release_channel = "STABLE"

  depends_on = [
    yandex_resourcemanager_folder_iam_member.cluster_agent,
    yandex_resourcemanager_folder_iam_member.vpc_public_admin,
    yandex_resourcemanager_folder_iam_member.lb_admin,
    yandex_resourcemanager_folder_iam_member.node_image_puller,
  ]
}

resource "yandex_kubernetes_node_group" "main" {
  cluster_id  = yandex_kubernetes_cluster.this.id
  name        = "${var.cluster_name}-pool"
  description = "Main node group for url-shortener workloads."

  version = var.k8s_version

  instance_template {
    platform_id = "standard-v3"

    resources {
      cores         = var.node_cores
      memory        = var.node_memory_gb
      core_fraction = 100
    }

    boot_disk {
      type = "network-ssd"
      size = var.node_disk_gb
    }

    network_interface {
      nat                = true
      subnet_ids         = [yandex_vpc_subnet.k8s.id]
      security_group_ids = [yandex_vpc_security_group.k8s_main.id]
    }

    container_runtime {
      type = "containerd"
    }
  }

  scale_policy {
    fixed_scale {
      size = var.node_count
    }
  }

  allocation_policy {
    location {
      zone = var.zone
    }
  }

  maintenance_policy {
    auto_upgrade = true
    auto_repair  = true

    maintenance_window {
      day        = "monday"
      start_time = "03:00"
      duration   = "3h"
    }
  }
}
