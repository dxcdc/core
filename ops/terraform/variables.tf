# CDC Core — Variáveis do Terraform

variable "vps_ip" {
  type        = string
  description = "Endereço IP principal da VPS de Produção CDC"
  default     = "76.13.227.135"
}

variable "vps_user" {
  type        = string
  description = "Usuário de acesso SSH à VPS"
  default     = "root"
}

variable "domain_name" {
  type        = string
  description = "Domínio principal do CDC Core"
  default     = "core.cdc.org.br"
}

variable "environment" {
  type        = string
  description = "Ambiente de execução (production, staging, dev)"
  default     = "production"
}

variable "app_name" {
  type        = string
  description = "Nome da aplicação Nave Mãe"
  default     = "cdc-core"
}
