from django.db import models

class UsuarioDataOps(models.Model):
    """Tabela de Monitoramento de Usuários (usuarios) - Google Workspace do CDC."""
    STATUS_CHOICES = (
        ('Ativo', 'Ativo'),
        ('Suspenso', 'Suspenso'),
        ('Inativo', 'Inativo'),
        ('Voluntário', 'Voluntário'),
        ('Alias', 'Apelido / Alias'),
    )

    email = models.EmailField(max_length=255, unique=True, verbose_name="E-mail Institucional")
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    setor_atual = models.CharField(max_length=100, default='Não Definido', verbose_name="Setor Atual")
    cota_total_gb = models.DecimalField(max_digits=6, decimal_places=2, default=50.00, verbose_name="Cota Total (GB)")
    cota_used_gb = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Cota Usada (GB)")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Ativo', verbose_name="Status da Conta")
    mfa_ativo = models.BooleanField(default=False, verbose_name="MFA/2FA Ativo")
    e_voluntario = models.BooleanField(default=False, verbose_name="É Voluntário")
    data_expiracao = models.DateField(null=True, blank=True, verbose_name="Data de Expiração do Contrato")
    ultimo_login = models.DateTimeField(null=True, blank=True, verbose_name="Último Login")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuário do Workspace"
        verbose_name_plural = "Usuários do Workspace"
        ordering = ['-criado_em']

    def porcentagem_uso(self):
        if self.cota_total_gb and self.cota_total_gb > 0:
            return round((float(self.cota_used_gb) / float(self.cota_total_gb)) * 100, 1)
        return 0.0

    def __str__(self):
        return f"{self.nome} ({self.email})"


class GrupoWorkspace(models.Model):
    """Cadastro de Grupos Institucionais do CDC (grupos)."""
    email_grupo = models.EmailField(max_length=255, unique=True, verbose_name="E-mail do Grupo")
    nome_grupo = models.CharField(max_length=255, verbose_name="Nome do Grupo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Grupo")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grupo do Workspace"
        verbose_name_plural = "Grupos do Workspace"

    def __str__(self):
        return f"{self.nome_grupo} <{self.email_grupo}>"


class MembroGrupo(models.Model):
    """Tabela Associativa de Vínculo de Membros nos Grupos (membros_grupos)."""
    grupo = models.ForeignKey(GrupoWorkspace, on_delete=models.CASCADE, related_name='membros')
    usuario = models.ForeignKey(UsuarioDataOps, on_delete=models.CASCADE, related_name='grupos_vinculados')
    vinculado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Membro de Grupo"
        verbose_name_plural = "Membros dos Grupos"
        unique_together = ('grupo', 'usuario')

    def __str__(self):
        return f"{self.usuario.nome} em {self.grupo.nome_grupo}"


class NotaFiscalConciliacao(models.Model):
    """Tabela de Notas Fiscais e Conciliação Financeira (notas_fiscais)."""
    STATUS_CHOICES = (
        ('Pendente', 'Pendente'),
        ('Conciliado', 'Conciliado'),
        ('Inconsistente', 'Inconsistente'),
    )

    chave_acesso = models.CharField(max_length=44, unique=True, verbose_name="Chave de Acesso (44 dígitos)")
    numero_nota = models.CharField(max_length=20, verbose_name="Número da Nota Fiscal")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")
    projeto_vinculado = models.CharField(max_length=100, verbose_name="Projeto Vinculado")
    status_conciliacao = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pendente', verbose_name="Status")
    importado_por = models.ForeignKey(UsuarioDataOps, on_delete=models.SET_NULL, null=True, blank=True)
    importado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nota Fiscal Conciliada"
        verbose_name_plural = "Notas Fiscais & Convênios"

    def __str__(self):
        return f"NF {self.numero_nota} - R$ {self.valor} ({self.projeto_vinculado})"


class LogAuditoria(models.Model):
    """Estrutura de Logs para Rastreamento Ético de Ações (logs_auditoria)."""
    STATUS_CHOICES = (
        ('INFO', 'Informação'),
        ('WARN', 'Alerta / Advertência'),
        ('SUCCESS', 'Sucesso'),
        ('ERROR', 'Erro / Inconsistência'),
    )

    usuario_executor = models.ForeignKey(UsuarioDataOps, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Executor")
    nivel = models.CharField(max_length=10, choices=STATUS_CHOICES, default='INFO', verbose_name="Nível")
    acao_executada = models.CharField(max_length=100, verbose_name="Ação Executada")
    alvo_impactado = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alvo Impactado")
    detalhes = models.TextField(verbose_name="Detalhes da Operação")
    ip_origem = models.CharField(max_length=45, default='127.0.0.1', verbose_name="IP de Origem")
    executado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora")

    class Meta:
        verbose_name = "Log de Auditoria DataOps"
        verbose_name_plural = "Logs de Auditoria DataOps"
        ordering = ['-executado_em']

    def __str__(self):
        return f"[{self.executado_em.strftime('%d/%m/%Y %H:%M')}] [{self.nivel}] {self.acao_executada} -> {self.alvo_impactado}"


class EstruturaVpn(models.Model):
    """Modelo para cadastro dinâmico de Estruturas, Setores da Sede e Projetos de Proteção no Mapa da VPN."""
    TIPO_CHOICES = (
        ('sede', 'Setor da Sede'),
        ('projeto', 'Projeto de Proteção à Vida'),
    )
    STATUS_CHOICES = (
        ('Online', 'Ligado (Online)'),
        ('Offline', 'Desligado (Offline)'),
    )

    nome = models.CharField(max_length=100, verbose_name="Nome da Estrutura / Setor")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sede', verbose_name="Ramo da Arquitetura")
    pcs_sede = models.IntegerField(default=1, verbose_name="Computadores da Sede")
    dispositivos_moveis = models.IntegerField(default=0, verbose_name="Celulares & Notebooks Externa")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Online', verbose_name="Status da Conexão")
    ip_faixa = models.CharField(max_length=50, default='10.8.x.x', verbose_name="Faixa de IP")
    latencia = models.CharField(max_length=20, default='12ms', verbose_name="Latência Média")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Estrutura de VPN"
        verbose_name_plural = "Estruturas de VPN"
        ordering = ['tipo', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()}) - {self.status}"


class CadastroSistema(models.Model):
    """Mapeamento e Cadastro de Sistemas / Aplicações Satélites do CDC."""
    CRITICIDADE_CHOICES = (
        ('Alta', 'Alta - Crítico'),
        ('Média', 'Média'),
        ('Baixa', 'Baixa'),
    )
    STATUS_CHOICES = (
        ('Operacional', 'Operacional / Em Produção'),
        ('Desenvolvimento', 'Em Desenvolvimento'),
        ('Legado', 'Sistema Legado'),
        ('Descontinuado', 'Descontinuado'),
    )

    nome_sistema = models.CharField(max_length=200, verbose_name="Nome do Sistema")
    sigla = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sigla / Código")
    responsavel_nome = models.CharField(max_length=150, verbose_name="Responsável Técnico")
    responsavel_email = models.EmailField(max_length=255, verbose_name="E-mail do Responsável")
    setor_projeto = models.CharField(max_length=100, verbose_name="Setor ou Projeto Vinculado")
    url_acesso = models.CharField(max_length=255, blank=True, null=True, verbose_name="URL de Acesso / IP")
    tecnologias = models.CharField(max_length=255, blank=True, null=True, verbose_name="Stack / Tecnologias")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Sistema")
    criticidade = models.CharField(max_length=20, choices=CRITICIDADE_CHOICES, default='Média', verbose_name="Criticidade")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Operacional', verbose_name="Status")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cadastro de Sistema"
        verbose_name_plural = "Cadastro dos Sistemas"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.nome_sistema} ({self.setor_projeto}) - {self.status}"


class RespostaFormulario(models.Model):
    """Armazenamento Único de Respostas de Formulários (Avaliação, Suporte, LGPD, etc)."""
    TIPO_CHOICES = (
        ('cadastro_sistema', 'Cadastro de Sistema'),
        ('avaliacao_servicos', 'Avaliação de Serviços & TI'),
        ('suporte_ti', 'Chamado de Suporte TI'),
        ('voluntario', 'Admissão de Voluntário'),
        ('termo_lgpd', 'Termo de Aceite LGPD'),
    )

    tipo_formulario = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo de Formulário")
    nome_respondente = models.CharField(max_length=150, verbose_name="Nome do Respondente")
    email_respondente = models.EmailField(max_length=255, verbose_name="E-mail")
    setor_ou_projeto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Setor / Projeto")
    avaliacao_nota = models.IntegerField(default=5, verbose_name="Nota de Satisfação (1-5)")
    assunto_ou_categoria = models.CharField(max_length=150, blank=True, null=True, verbose_name="Assunto / Categoria")
    mensagem_detalhes = models.TextField(verbose_name="Mensagem / Detalhes")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Resposta de Formulário"
        verbose_name_plural = "Respostas de Formulários"
        ordering = ['-criado_em']

    def __str__(self):
        return f"[{self.get_tipo_formulario_display()}] {self.nome_respondente} ({self.criado_em.strftime('%d/%m/%Y %H:%M')})"
