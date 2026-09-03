# CDC Core — Outputs do Terraform

output "master_control_hub" {
  value = {
    app_name    = var.app_name
    environment = var.environment
    domain      = "https://${var.domain_name}"
    vps_target  = "${var.vps_user}@${var.vps_ip}"
  }
  description = "Informações do Hub Nave Mãe cadastrado no Terraform"
}
