# CDC Core — Infrastructure as Code (Nave Mãe)
# Configuração Principal do Terraform

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
  }
}

# Provider Local para Execuções e Orquestração
provider "null" {}

# Definição dos Servidores Gerenciados pela Nave Mãe
resource "null_resource" "vps_production_node" {
  triggers = {
    vps_ip   = var.vps_ip
    app_name = var.app_name
  }

  provisioner "local-exec" {
    command = "echo 'Nave Mãe conectada à VPS de Produção: ${var.vps_ip}'"
  }
}
