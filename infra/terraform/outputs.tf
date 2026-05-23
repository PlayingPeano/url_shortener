output "vm_id" {
  description = "Compute instance ID."
  value       = yandex_compute_instance.this.id
}

output "vm_public_ip" {
  description = "Public IPv4 address assigned by Yandex Cloud NAT."
  value       = yandex_compute_instance.this.network_interface[0].nat_ip_address
}

output "vm_internal_ip" {
  description = "Internal IPv4 address inside the VPC subnet."
  value       = yandex_compute_instance.this.network_interface[0].ip_address
}

output "ssh_hint" {
  description = "Ready-to-copy SSH command (substitute path to your private key)."
  value       = "ssh -i ~/.ssh/url_shortener_deploy ${var.vm_user}@${yandex_compute_instance.this.network_interface[0].nat_ip_address}"
}
