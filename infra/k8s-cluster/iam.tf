resource "yandex_iam_service_account" "cluster" {
  name        = "${var.cluster_name}-cluster-sa"
  description = "Service account used by the K8s control plane."
}

resource "yandex_iam_service_account" "nodes" {
  name        = "${var.cluster_name}-nodes-sa"
  description = "Service account used by K8s worker nodes (image pulling)."
}

resource "yandex_resourcemanager_folder_iam_member" "cluster_agent" {
  folder_id = var.folder_id
  role      = "k8s.clusters.agent"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "vpc_public_admin" {
  folder_id = var.folder_id
  role      = "vpc.publicAdmin"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "lb_admin" {
  folder_id = var.folder_id
  role      = "load-balancer.admin"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "kms_encrypter_decrypter" {
  folder_id = var.folder_id
  role      = "kms.keys.encrypterDecrypter"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "node_image_puller" {
  folder_id = var.folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.nodes.id}"
}

resource "yandex_iam_service_account" "ci_pusher" {
  name        = "${var.cluster_name}-ci-pusher"
  description = "Service account used by GitHub Actions to push images to CR and roll out deployments in K8s."
}

resource "yandex_resourcemanager_folder_iam_member" "ci_images_pusher" {
  folder_id = var.folder_id
  role      = "container-registry.images.pusher"
  member    = "serviceAccount:${yandex_iam_service_account.ci_pusher.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "ci_k8s_editor" {
  folder_id = var.folder_id
  role      = "k8s.cluster-api.editor"
  member    = "serviceAccount:${yandex_iam_service_account.ci_pusher.id}"
}
