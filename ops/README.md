# 🛸 Orquestração de Infraestrutura & Configurações — CDC Core (Nave Mãe)

Este diretório contém a estrutura de **Infraestrutura como Código (IaC)** e **Gestão de Configurações** do Centro Dom Helder Camara (CDC), utilizando **Terraform** e **Ansible**.

---

## 📁 Estrutura de Diretórios

* `terraform/`: Declaração e provisionamento de recursos de infraestrutura.
  * `main.tf`: Definições principais e provedores.
  * `variables.tf`: Variáveis de ambiente e parâmetros.
  * `outputs.tf`: Informações de saída expostas pelo Terraform.
* `ansible/`: Automação, configuração e gerenciamento de servidores.
  * `ansible.cfg`: Configurações globais do Ansible.
  * `inventory/production.ini`: Inventário dos servidores gerenciados (ex: VPS `76.13.xxx.xxx`).
  * `playbooks/`:
    * `01_setup_server.yml`: Fortalecimento, atualização de SO e preparação do servidor.
    * `02_deploy_core.yml`: Deploy automatizado, migrações e arquivos estáticos.
    * `03_system_health.yml`: Relatório e checkup de saúde do servidor e containers.

---

## 🛠️ Como Executar

### 1. Terraform
```bash
cd ops/terraform
terraform init
terraform plan
terraform apply
```

### 2. Ansible
```bash
cd ops/ansible

# Testar conectividade SSH com a VPS
ansible production_vps -m ping

# Executar checkup de saúde do servidor
ansible-playbook playbooks/03_system_health.yml

# Executar rotina de deploy
ansible-playbook playbooks/02_deploy_core.yml
```
