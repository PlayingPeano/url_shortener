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

output "ci_pusher_sa_id" {
  description = "Service account used by GitHub Actions for image push & K8s rollout."
  value       = yandex_iam_service_account.ci_pusher.id
}

output "ci_pusher_create_key_command" {
  description = "Create a JSON-key for the CI service account (the file then goes into GitHub secret YC_SA_JSON_KEY)."
  value       = "yc iam key create --service-account-id ${yandex_iam_service_account.ci_pusher.id} --output sa-key.json"
}

output "folder_id" {
  description = "Folder ID where the K8s cluster + registry live (paste into GitHub secret YC_FOLDER_ID)."
  value       = var.folder_id
}
