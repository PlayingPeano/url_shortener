output "cluster_id" {
  description = "Managed K8s cluster ID."
  value       = yandex_kubernetes_cluster.this.id
}

output "cluster_name" {
  description = "Managed K8s cluster name."
  value       = yandex_kubernetes_cluster.this.name
}

output "node_group_id" {
  description = "Main node group ID."
  value       = yandex_kubernetes_node_group.main.id
}

output "registry_id" {
  description = "Yandex Container Registry ID (used in image refs as cr.yandex/<id>/...)."
  value       = yandex_container_registry.main.id
}

output "kubeconfig_command" {
  description = "Run this command (with yc CLI installed) to write ~/.kube/config for kubectl access."
  value       = "yc managed-kubernetes cluster get-credentials --id ${yandex_kubernetes_cluster.this.id} --external --force"
}

output "registry_login_command" {
  description = "Run this to log Docker into the registry for image pushes."
  value       = "yc container registry configure-docker"
}
