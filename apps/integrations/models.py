import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


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


class OngsysNotaServico(models.Model):
    id_ongsys = models.CharField(max_length=64, unique=True, db_index=True)
    numero_nota = models.CharField(max_length=64, blank=True, db_index=True)
    codigo_verificacao = models.CharField(max_length=64, blank=True)
    prestador_nome = models.CharField(max_length=255, blank=True)
    prestador_documento = models.CharField(max_length=32, blank=True, db_index=True)
    tomador_nome = models.CharField(max_length=255, blank=True)
    tomador_documento = models.CharField(max_length=32, blank=True, db_index=True)
    data_emissao = models.DateField(null=True, blank=True, db_index=True)
    data_competencia = models.DateField(null=True, blank=True)
    valor_servicos = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    valor_liquido = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    discriminacao_servicos = models.TextField(blank=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Fiscal de Serviço (NFS-e)"
        verbose_name_plural = "Notas Fiscais de Serviço (NFS-e)"
        ordering = ["-data_emissao", "-criado_em"]

    def __str__(self):
        return f"NFS-e {self.numero_nota} - {self.prestador_nome} (R$ {self.valor_servicos})"


class OngsysNotaProduto(models.Model):
    id_ongsys = models.CharField(max_length=64, unique=True, db_index=True)
    numero_nfe = models.CharField(max_length=64, blank=True, db_index=True)
    serie = models.CharField(max_length=16, blank=True)
    chave_acesso = models.CharField(max_length=44, blank=True, db_index=True)
    emitente_nome = models.CharField(max_length=255, blank=True)
    emitente_documento = models.CharField(max_length=32, blank=True, db_index=True)
    destinatario_nome = models.CharField(max_length=255, blank=True)
    destinatario_documento = models.CharField(max_length=32, blank=True, db_index=True)
    data_emissao = models.DateField(null=True, blank=True, db_index=True)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    natureza_operacao = models.CharField(max_length=255, blank=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota Fiscal de Produto (NF-e)"
        verbose_name_plural = "Notas Fiscais de Produto (NF-e)"
        ordering = ["-data_emissao", "-criado_em"]

    def __str__(self):
        return f"NF-e {self.numero_nfe} - {self.emitente_nome} (R$ {self.valor_total})"


class OngsysEndpointStatus(models.Model):

    class Classificacao(models.TextChoices):
        SUCCESS = "success", "Operacional (HTTP 200)"
        VALIDATED = "validated", "Requer Parâmetros (HTTP 422)"
        ERROR = "error", "Com Falha / Erro"
        UNTESTED = "untested", "Não Testado"

    endpoint_id = models.CharField(max_length=64, unique=True, db_index=True)
    endpoint_path = models.CharField(max_length=120)
    metodo = models.CharField(max_length=10, default="GET")
    ultimo_status_http = models.IntegerField(null=True, blank=True)
    status_classificacao = models.CharField(
        max_length=32,
        choices=Classificacao.choices,
        default=Classificacao.UNTESTED
    )
    latencia_ms = models.IntegerField(default=0)
    ultima_vez_testado = models.DateTimeField(null=True, blank=True)
    ultima_vez_sucesso = models.DateTimeField(null=True, blank=True)
    detalhes_resposta = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Status de Endpoint OngSys"
        verbose_name_plural = "Status de Endpoints OngSys"
        ordering = ["endpoint_id"]
        permissions = [
            ("test_ongsys_api", "Pode executar testes de leitura na API OngSys"),
            ("sync_ongsys_data", "Pode sincronizar dados da API OngSys"),
            ("view_ongsys_report", "Pode visualizar relatórios da integração OngSys"),
        ]

    def __str__(self):
        return f"{self.endpoint_id} - HTTP {self.ultimo_status_http} ({self.status_classificacao})"


class OngsysTask(models.Model):
    class Tipo(models.TextChoices):
        TEST_ALL = "test_all", "Testar rotas de leitura"
        SYNC_DB = "sync_db", "Sincronizar banco"

    class Status(models.TextChoices):
        QUEUED = "queued", "Na fila"
        RUNNING = "running", "Em execução"
        COMPLETED = "completed", "Concluída"
        PARTIAL = "partial", "Concluída parcialmente"
        ERROR = "error", "Com erro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=16, choices=Tipo.choices)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ongsys_tasks",
    )
    entidade = models.CharField(max_length=32, default="all")
    paginas = models.PositiveSmallIntegerField(default=1)
    progresso_pct = models.PositiveSmallIntegerField(default=0)
    etapa_atual = models.CharField(max_length=255, blank=True)
    total_itens = models.PositiveSmallIntegerField(default=0)
    itens_concluidos = models.PositiveSmallIntegerField(default=0)
    resultados = models.JSONField(default=list, blank=True)
    erro = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    iniciado_em = models.DateTimeField(null=True, blank=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tarefa OngSys"
        verbose_name_plural = "Tarefas OngSys"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "entidade"],
                condition=Q(status="running"),
                name="uniq_running_ongsys_task_entity",
            )
        ]

    def __str__(self):
        return f"{self.tipo}:{self.entidade} ({self.status})"


class OngsysAuditLog(models.Model):
    """
    Trilha de Auditoria e Governança da API OngSys (/logs).
    Registra ações de usuários, logins, inclusões, alterações e exclusões com integridade transacional.
    """
    log_id = models.CharField(max_length=32, unique=True, db_index=True)
    usuario_id = models.CharField(max_length=32, blank=True, db_index=True)
    usuario_nome = models.CharField(max_length=255, blank=True, db_index=True)
    origem = models.CharField(max_length=120, blank=True, db_index=True)
    descricao_transacao = models.TextField(blank=True)
    data_evento = models.DateTimeField(null=True, blank=True, db_index=True)
    dados_brutos = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Log de Auditoria OngSys"
        verbose_name_plural = "Logs de Auditoria OngSys"
        ordering = ["-data_evento", "-log_id"]
        indexes = [
            models.Index(fields=["usuario_nome", "data_evento"]),
            models.Index(fields=["origem", "data_evento"]),
        ]

    def __str__(self):
        return f"Log #{self.log_id} - {self.usuario_nome} ({self.origem}) [{self.data_evento}]"


# ==============================================================================
# TRANSPORTES & MOBILIDADE ATÔMICA (UBER & 99)
# ==============================================================================
class TransporteCorrida(models.Model):
    """
    Registro Atômico de Corridas & Deslocamentos Corporativos (Uber & 99).
    Armazena as 22 colunas oficiais para prestação de contas, conciliação e API REST.
    """
    class Plataforma(models.TextChoices):
        UBER = "Uber", "Uber"
        NOVENOVE = "99", "99"

    id_corrida = models.CharField(max_length=128, db_index=True, verbose_name="ID da Corrida")
    plataforma = models.CharField(max_length=16, choices=Plataforma.choices, default=Plataforma.UBER, db_index=True)

    # Datas e Horas (Formatos oficiais do relatório e DateTimeField para consultas rápidas)
    data_solicitacao = models.CharField(max_length=32, blank=True, verbose_name="Data Solicitação")
    hora_solicitacao = models.CharField(max_length=32, blank=True, verbose_name="Hora Solicitação")
    data_chegada = models.CharField(max_length=32, blank=True, verbose_name="Data Chegada")
    hora_chegada = models.CharField(max_length=32, blank=True, verbose_name="Hora Chegada")
    solicitado_em = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Data/Hora Início")
    concluido_em = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Data/Hora Fim")

    # Classificação
    servico = models.CharField(max_length=120, blank=True, verbose_name="Serviço")
    programa = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Programa / Projeto")
    grupo = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Grupo / Centro de Custo")

    # Colaborador / Passageiro
    nome = models.CharField(max_length=120, blank=True, verbose_name="Nome")
    sobrenome = models.CharField(max_length=120, blank=True, verbose_name="Sobrenome")
    nome_completo = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Nome Completo")
    email = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Email")

    # Despesas e Métricas
    detalhamento_despesa = models.TextField(blank=True, verbose_name="Detalhamento da despesa")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, db_index=True, verbose_name="Valor Total")
    distancia_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Distância (km)")
    duracao_minutos = models.IntegerField(null=True, blank=True, verbose_name="Duração (min)")

    # Localização
    endereco_partida = models.TextField(blank=True, verbose_name="Endereço Partida")
    endereco_destino = models.TextField(blank=True, verbose_name="Endereço Destino")
    cidade = models.CharField(max_length=120, blank=True, db_index=True, verbose_name="Cidade")
    pais = models.CharField(max_length=64, default="Brasil", verbose_name="País")
    status = models.CharField(max_length=64, default="Concluída", db_index=True, verbose_name="Status")

    # Rastreabilidade e Auditoria
    arquivo_origem = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Arquivo de Origem")
    dados_brutos = models.JSONField(default=dict, blank=True, verbose_name="Dados Brutos JSON")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Corrida de Transporte (Uber/99)"
        verbose_name_plural = "Corridas de Transporte (Uber/99)"
        ordering = ["-solicitado_em", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["id_corrida", "plataforma"],
                name="uniq_transporte_corrida_plataforma"
            )
        ]
        indexes = [
            models.Index(fields=["plataforma", "solicitado_em"]),
            models.Index(fields=["programa", "solicitado_em"]),
            models.Index(fields=["grupo", "solicitado_em"]),
            models.Index(fields=["nome_completo", "solicitado_em"]),
        ]

    def __str__(self):
        return f"[{self.plataforma}] {self.id_corrida} - {self.nome_completo} (R$ {self.valor_total})"
