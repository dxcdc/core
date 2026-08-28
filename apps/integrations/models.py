from django.db import models


class IntegrationSystem(models.Model):
    class Direction(models.TextChoices):
        SOURCE = "source", "Fonte de dados"
        DESTINATION = "destination", "Destino de dados"
        BIDIRECTIONAL = "bidirectional", "Bidirecional"

    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    base_url = models.URLField(blank=True)
    direction = models.CharField(max_length=16, choices=Direction.choices)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class IntegrationSyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Em execução"
        SUCCEEDED = "succeeded", "Concluída"
        FAILED = "failed", "Falhou"

    system = models.ForeignKey(IntegrationSystem, on_delete=models.PROTECT)
    dataset = models.CharField(max_length=64)
    correlation_id = models.UUIDField(unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    contract_version = models.CharField(max_length=16, default="v1")
    modified_since = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    pages_processed = models.PositiveIntegerField(default=0)
    records_received = models.PositiveIntegerField(default=0)
    records_inserted = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    last_cursor = models.TextField(blank=True)
    error_code = models.CharField(max_length=80, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]


class IntegrationCheckpoint(models.Model):
    system = models.ForeignKey(IntegrationSystem, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=64)
    completed_through = models.DateTimeField(null=True, blank=True)
    resume_cursor = models.TextField(blank=True)
    resume_modified_since = models.DateTimeField(null=True, blank=True)
    last_run = models.ForeignKey(
        IntegrationSyncRun, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("system", "dataset"), name="uniq_checkpoint_system_dataset"
            )
        ]


class IntegrationStagingRecord(models.Model):
    system = models.ForeignKey(IntegrationSystem, on_delete=models.PROTECT)
    dataset = models.CharField(max_length=64)
    source_name = models.CharField(max_length=255)
    source_modified = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField()
    contract_version = models.CharField(max_length=16)
    imported_by_run = models.ForeignKey(IntegrationSyncRun, on_delete=models.PROTECT)
    ingested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("system", "dataset", "source_name"),
                name="uniq_staging_source_dataset_name",
            )
        ]
        indexes = [models.Index(fields=("system", "dataset", "source_modified"))]


class Warehouse(models.Model):
    system = models.ForeignKey(IntegrationSystem, on_delete=models.PROTECT)
    source_name = models.CharField(max_length=255)
    warehouse_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=120, blank=True)
    source_modified = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    imported_by_run = models.ForeignKey(IntegrationSyncRun, on_delete=models.PROTECT)
    ingested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("system", "source_name"), name="uniq_warehouse_system_name"
            )
        ]


# ==============================================================================
# 🏢 MODELOS ATÔMICOS DE DADOS DA ONGSYS (ESPELHO TRANSACIONAL POSTGRESQL)
# ==============================================================================

class OngsysFornecedor(models.Model):
    id_ongsys = models.CharField(max_length=64, unique=True, db_index=True)
    documento = models.CharField(max_length=32, blank=True, db_index=True)
    nome_empresa = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    tipo_pessoa = models.CharField(max_length=32, blank=True, null=True)
    tipo_fornecedor = models.CharField(max_length=64, blank=True, null=True)
    ativo_inativo = models.CharField(max_length=8, default="A")
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fornecedor OngSys"
        verbose_name_plural = "Fornecedores OngSys"
        ordering = ["nome_empresa"]

    def __str__(self):
        return f"{self.nome_empresa} ({self.documento})"


class OngsysCliente(models.Model):
    id_ongsys = models.CharField(max_length=64, unique=True, db_index=True)
    documento = models.CharField(max_length=32, blank=True, db_index=True)
    nome_empresa = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    tipo_pessoa = models.CharField(max_length=32, blank=True, null=True)
    tipo_cliente = models.CharField(max_length=64, blank=True, null=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente / Projeto OngSys"
        verbose_name_plural = "Clientes / Projetos OngSys"
        ordering = ["nome_empresa"]

    def __str__(self):
        return f"{self.nome_empresa} ({self.documento})"


class OngsysContaPagar(models.Model):
    cod_lancamento = models.CharField(max_length=64, unique=True, db_index=True)
    fornecedor_nome = models.CharField(max_length=255, blank=True)
    fornecedor_documento = models.CharField(max_length=32, blank=True)
    historico_despesa = models.TextField(blank=True)
    tipo_despesa = models.CharField(max_length=120, blank=True)
    data_emissao = models.DateField(null=True, blank=True, db_index=True)
    data_vencimento = models.DateField(null=True, blank=True, db_index=True)
    data_pagamento = models.DateField(null=True, blank=True, db_index=True)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    valor_pago = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    status_pagamento = models.CharField(max_length=64, blank=True)
    projeto_nome = models.CharField(max_length=255, blank=True, db_index=True)
    subprojeto_nome = models.CharField(max_length=255, blank=True)
    conta_contabil = models.CharField(max_length=255, blank=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conta a Pagar OngSys"
        verbose_name_plural = "Contas a Pagar OngSys"
        ordering = ["-data_vencimento", "-criado_em"]

    def __str__(self):
        return f"{self.cod_lancamento} - {self.fornecedor_nome} (R$ {self.valor_total})"


class OngsysContaReceber(models.Model):
    cod_lancamento = models.CharField(max_length=64, unique=True, db_index=True)
    cliente_nome = models.CharField(max_length=255, blank=True)
    cliente_documento = models.CharField(max_length=32, blank=True)
    data_emissao = models.DateField(null=True, blank=True, db_index=True)
    data_vencimento = models.DateField(null=True, blank=True, db_index=True)
    data_recebimento = models.DateField(null=True, blank=True, db_index=True)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    valor_recebido = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    projeto_nome = models.CharField(max_length=255, blank=True, db_index=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conta a Receber OngSys"
        verbose_name_plural = "Contas a Receber OngSys"
        ordering = ["-data_vencimento", "-criado_em"]

    def __str__(self):
        return f"{self.cod_lancamento} - {self.cliente_nome} (R$ {self.valor_total})"


class OngsysLancamentoBancario(models.Model):
    codigo = models.CharField(max_length=64, unique=True, db_index=True)
    data_operacao = models.DateField(null=True, blank=True, db_index=True)
    conta_bancaria = models.CharField(max_length=255, blank=True)
    tipo_operacao = models.CharField(max_length=16, blank=True)  # D: Débito / C: Crédito
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    categoria = models.CharField(max_length=120, blank=True)
    descricao = models.TextField(blank=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lançamento Bancário OngSys"
        verbose_name_plural = "Lançamentos Bancários OngSys"
        ordering = ["-data_operacao", "-criado_em"]

    def __str__(self):
        return f"{self.codigo} - {self.conta_bancaria} (R$ {self.valor})"


class OngsysContrato(models.Model):
    id_ongsys = models.CharField(max_length=64, unique=True, db_index=True)
    codigo = models.CharField(max_length=64, blank=True)
    tipo_contrato = models.CharField(max_length=32, default="PAGAR")  # PAGAR ou RECEBER
    nome_contraparte = models.CharField(max_length=255, blank=True)
    documento_contraparte = models.CharField(max_length=32, blank=True)
    nome_contrato = models.CharField(max_length=255)
    descricao_contrato = models.TextField(blank=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrato OngSys"
        verbose_name_plural = "Contratos OngSys"
        ordering = ["nome_contrato"]

    def __str__(self):
        return f"[{self.tipo_contrato}] {self.codigo} - {self.nome_contrato}"


class OngsysProduto(models.Model):
    id_ongsys = models.CharField(max_length=64, unique=True, db_index=True)
    nome_produto = models.CharField(max_length=255)
    descricao_produto = models.TextField(blank=True)
    status = models.CharField(max_length=32, default="ativo")
    grupo = models.CharField(max_length=120, blank=True, null=True)
    unidade_medida = models.CharField(max_length=64, blank=True, null=True)
    valor_custo = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto OngSys"
        verbose_name_plural = "Produtos OngSys"
        ordering = ["nome_produto"]

    def __str__(self):
        return f"{self.nome_produto} ({self.grupo})"

