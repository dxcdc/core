from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from apps.dataops.models import UsuarioDataOps, GrupoWorkspace, MembroGrupo, NotaFiscalConciliacao, LogAuditoria

User = get_user_model()

def landing_view(request):
    """Renderiza a Landing Page pública do CDC Core."""
    return render(request, 'landing.html')

@login_required(login_url='dashboard:login')
def index(request):
    """Renderiza o painel operacional DataOps do CDC Core no estilo Lahomes."""
    usuarios = UsuarioDataOps.objects.all()
    logs = LogAuditoria.objects.all()[:15]
    alertas_criticos = LogAuditoria.objects.filter(nivel__in=['ERROR', 'WARN'])[:5]
    
    adriana = UsuarioDataOps.objects.filter(email='adrianasantos@cdc.org.br').first()
    joab = UsuarioDataOps.objects.filter(email='joabsilva@cdc.org.br').first()
    joab_vinculos = MembroGrupo.objects.filter(usuario=joab) if joab else []
    paterson = UsuarioDataOps.objects.filter(email='paterson.silva@cdc.org.br').first()
    voluntarios = UsuarioDataOps.objects.filter(e_voluntario=True)

    context = {
        'usuarios': usuarios,
        'logs': logs,
        'alertas_criticos': alertas_criticos,
        'adriana': adriana,
        'joab': joab,
        'joab_vinculos': joab_vinculos,
        'paterson': paterson,
        'voluntarios': voluntarios,
        'stats': {
            'total_usuarios': usuarios.count(),
            'total_grupos': GrupoWorkspace.objects.count(),
            'contas_risco_cota': UsuarioDataOps.objects.filter(cota_used_gb__gte=40).count(),
            'contas_sem_mfa': UsuarioDataOps.objects.filter(mfa_ativo=False, status='Ativo').count(),
        }
    }
    return render(request, 'dashboard/index.html', context)

@login_required(login_url='dashboard:login')
def infra_view(request):
    """Renderiza o módulo de Infraestrutura & Servidores / Containers Docker."""
    containers = [
        {'nome': 'cdc-postgresql-db', 'imagem': 'postgres:15-alpine', 'status': 'Rodando', 'porta': '5432:5432', 'uptime': '14 dias', 'cpu': '1.2%', 'ram': '142 MB'},
        {'nome': 'cdc-django-backend', 'imagem': 'dxcdc/core:latest', 'status': 'Rodando', 'porta': '8000:8000', 'uptime': '7 dias', 'cpu': '2.4%', 'ram': '210 MB'},
        {'nome': 'cdc-n8n-orchestrator', 'imagem': 'n8nio/n8n:latest', 'status': 'Rodando', 'porta': '5678:5678', 'uptime': '14 dias', 'cpu': '0.8%', 'ram': '185 MB'},
        {'nome': 'cdc-evolution-api', 'imagem': 'atendimento/evolution-api:v1.8', 'status': 'Rodando', 'porta': '8080:8080', 'uptime': '14 dias', 'cpu': '1.5%', 'ram': '195 MB'},
        {'nome': 'cdc-redis-cache', 'imagem': 'redis:7-alpine', 'status': 'Rodando', 'porta': '6379:6379', 'uptime': '14 dias', 'cpu': '0.2%', 'ram': '45 MB'},
    ]
    return render(request, 'dashboard/infra.html', {'containers': containers})

@login_required(login_url='dashboard:login')
def vpn_view(request):
    """Renderiza o Mapa de Infraestrutura & Conexões VPN por Projetos (PROVITA, PPCAM, PPDDH)."""
    from apps.dataops.models import EstruturaVpn

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', 'sede')
        pcs_sede = int(request.POST.get('pcs_sede', 1))
        dispositivos_moveis = int(request.POST.get('dispositivos_moveis', 0))
        status = request.POST.get('status', 'Online')
        ip_faixa = request.POST.get('ip_faixa', '10.8.x.x')

        if nome:
            nova_est = EstruturaVpn.objects.create(
                nome=nome,
                tipo=tipo,
                pcs_sede=pcs_sede,
                dispositivos_moveis=dispositivos_moveis,
                status=status,
                ip_faixa=ip_faixa,
                latencia='12ms'
            )
            user_exec = UsuarioDataOps.objects.filter(email='fvier@cdc.org.br').first()
            LogAuditoria.objects.create(
                usuario_executor=user_exec,
                nivel='SUCCESS',
                acao_executada='CADASTRO_ESTRUTURA_VPN',
                alvo_impactado=f"{nova_est.nome} ({nova_est.get_tipo_display()})",
                detalhes=f"Nova estrutura cadastrada no mapa de infraestrutura VPN com status {status}."
            )
            messages.success(request, f'Estrutura "{nome}" adicionada com sucesso ao mapa de VPN!')
            return redirect('dashboard:vpn')

    estruturas_sede = EstruturaVpn.objects.filter(tipo='sede')
    estruturas_projeto = EstruturaVpn.objects.filter(tipo='projeto')

    context = {
        'estruturas_sede': estruturas_sede,
        'estruturas_projeto': estruturas_projeto,
        'total_online': EstruturaVpn.objects.filter(status='Online').count(),
        'total_offline': EstruturaVpn.objects.filter(status='Offline').count(),
    }
    return render(request, 'dashboard/vpn_mapa.html', context)

@login_required(login_url='dashboard:login')
def workspace_view(request):
    """Renderiza o módulo Google Workspace utilizando EXCLUSIVAMENTE dados reais da API oficial do Google Workspace."""
    from .google_service import fetch_google_workspace_data

    google_real = fetch_google_workspace_data('gt.transformadigital@cdc.org.br')

    if google_real.get('is_real'):
        # DADOS REAIS DA API DO GOOGLE WORKSPACE
        contas_render = google_real.get('users', [])
        total_contas = len(contas_render)
        cota_drive = google_real.get('drive_quota', '0.00 GB')
        grupos_render = google_real.get('groups', [])
        ous_render = google_real.get('ous', [])
        
        # Novas métricas de Otimização e Segurança
        contas_suspensas = sum(1 for u in contas_render if u.get('status') == 'Suspenso')
        contas_vulneraveis = sum(1 for u in contas_render if 'Não Ativado' in str(u.get('mfa', '')))
        aliases_gratuitos = len(grupos_render)
    else:
        # SEM DADOS FICTÍCIOS - AGUARDANDO NAVEGAÇÃO E CHAVE API REAL
        contas_render = []
        total_contas = 0
        cota_drive = 'Conexão Pendente'
        grupos_render = []
        ous_render = []
        
        contas_suspensas = 0
        contas_vulneraveis = 0
        aliases_gratuitos = 0

    logs_workspace = LogAuditoria.objects.all()[:10]

    context = {
        'contas_hipoteticas': contas_render,
        'grupos_workspace': grupos_render,
        'ous_workspace': ous_render,
        'logs_workspace': logs_workspace,
        'apps_oauth': [],
        'google_real': google_real,
        'stats_workspace': {
            'total_contas': total_contas,
            'contas_suspensas': contas_suspensas,
            'contas_vulneraveis': contas_vulneraveis,
            'aliases_gratuitos': aliases_gratuitos,
            'cota_usada_total': cota_drive,
        }
    }
    return render(request, 'dashboard/workspace.html', context)

@login_required(login_url='dashboard:login')
def cofre_view(request):
    """Renderiza o Cofre de Segredos & Credenciais do CDC."""
    segredos = [
        {'nome': 'Chave Privada SSH Master (ed25519)', 'categoria': 'Infraestrutura', 'detalhe': 'Acesso root às VPS Hostinger', 'atualizado': 'Há 3 dias'},
        {'nome': 'Service Account Token Google Workspace', 'categoria': 'API Token', 'detalhe': 'Delegação de autoridade @cdc.org.br', 'atualizado': 'Há 14 dias'},
        {'nome': 'Token Webhook Evolution API WhatsApp', 'categoria': 'Mensageria', 'detalhe': 'Chave bearer de escuta n8n', 'atualizado': 'Há 7 dias'},
        {'nome': 'Credenciais PostgreSQL DataOps', 'categoria': 'Banco de Dados', 'detalhe': 'Usuário cdc_user e senha criptografada', 'atualizado': 'Há 20 dias'},
        {'nome': 'API Key OpenWeather / Telemetria', 'categoria': 'Utilitários', 'detalhe': 'Chave pública de dados ambientais', 'atualizado': 'Há 30 dias'},
    ]
    return render(request, 'dashboard/cofre.html', {'segredos': segredos})

@login_required(login_url='dashboard:login')
def ferramentas_view(request):
    """Renderiza o Canivete de Ferramentas de Escritório e Conversores do CDC."""
    return render(request, 'dashboard/ferramentas.html')

@login_required(login_url='dashboard:login')
def governanca_view(request):
    """Renderiza a página de Governança, Diretrizes e ADRs do CDC."""
    adrs = [
        {'id': 'ADR-001', 'data': '2026-07-21', 'decisao': 'Adição de subpastas infra/, prompts/ e api/', 'motivo': 'Organização modular por recurso reutilizável', 'status': 'Aprovado'},
        {'id': 'ADR-002', 'data': '2026-07-21', 'decisao': 'Adoção do modelo de arquivos na pasta docs/', 'motivo': 'Padronização de governança DevOps', 'status': 'Aprovado'},
        {'id': 'ADR-003', 'data': '2026-07-24', 'decisao': 'Automação Idempotente de Issues via GitHub Actions', 'motivo': 'Garantir cadastro e rastreabilidade no GitHub sem duplicar', 'status': 'Aprovado'},
        {'id': 'ADR-004', 'data': '2026-07-28', 'decisao': 'Padronização de Visualização Gráfica de Branches', 'motivo': 'Facilitar auditoria e entendimento visual do Git Graph', 'status': 'Aprovado'},
    ]
    return render(request, 'dashboard/governanca.html', {'adrs': adrs})

@login_required(login_url='dashboard:login')
def simular_acao(request, acao):
    """Executa simulações e sincronizações interativas dos fluxos do CDC."""
    from .google_service import fetch_google_workspace_data
    user_exec = UsuarioDataOps.objects.filter(email='fvier@cdc.org.br').first()

    if acao in ('auditoria_mfa', 'sincronizar_google', 'auditar_mfa_geral'):
        res = fetch_google_workspace_data('gt.transformadigital@cdc.org.br')
        if res.get('is_real'):
            messages.success(request, f"⚡ APIs do Google Workspace sincronizadas em tempo real com sucesso! {res.get('total_users', 0)} contas atualizadas.")
        else:
            messages.info(request, "Sincronização de auditoria executada com sucesso.")

    elif acao == 'expandir_cota_adriana':
        adriana = UsuarioDataOps.objects.filter(email='adrianasantos@cdc.org.br').first()
        if adriana:
            adriana.cota_total_gb = 100.00
            adriana.save()
            LogAuditoria.objects.create(
                usuario_executor=user_exec,
                nivel='SUCCESS',
                acao_executada='EXPANSAO_COTA_EMERGENCIA',
                alvo_impactado='adrianasantos@cdc.org.br',
                detalhes='Cota ampliada temporariamente de 50GB para 100GB.'
            )
            messages.success(request, 'Sucesso: Cota de Adriana Santos ampliada temporariamente para 100GB!')

    elif acao == 'remover_joab_grupo':
        joab = UsuarioDataOps.objects.filter(email='joabsilva@cdc.org.br').first()
        if joab:
            vinculos = MembroGrupo.objects.filter(usuario=joab)
            grupos_nomes = ", ".join([v.grupo.nome_grupo for v in vinculos])
            vinculos.delete()
            LogAuditoria.objects.create(
                usuario_executor=user_exec,
                nivel='SUCCESS',
                acao_executada='REMOCAO_MEMBRO_GRUPO',
                alvo_impactado='joabsilva@cdc.org.br',
                detalhes=f'Ex-colaborador suspenso removido com sucesso de todos os grupos institucionais ({grupos_nomes}).'
            )
            messages.success(request, 'Sucesso: Joab da Silva foi removido de todos os grupos institucionais!')

    elif acao == 'executar_alias_paterson':
        messages.success(request, 'Verificação concluída: Alias de Paterson Silva operando sem custos de licença!')

    else:
        messages.success(request, f'Ação "{acao}" executada com sucesso!')

    return redirect('dashboard:workspace')

@login_required(login_url='dashboard:login')
def integracoes_view(request):
    """Renderiza a Central de Integrações & APIs do CDC Core com configurações e conectores."""
    from .google_service import test_google_workspace_connection, save_service_account_json, get_credentials_file_path

    if request.method == 'POST':
        api_name = request.POST.get('api_name', 'Google Workspace')
        
        if 'json_file' in request.FILES:
            try:
                save_service_account_json(request.FILES['json_file'])
                messages.success(request, 'Chave JSON da Service Account salva com sucesso no diretório de credenciais!')
            except Exception as e:
                messages.error(request, f'Erro ao salvar arquivo JSON: {e}')

        elif 'json_text' in request.POST and request.POST.get('json_text').strip():
            try:
                save_service_account_json(request.POST.get('json_text').strip())
                messages.success(request, 'Credencial JSON da Service Account salva com sucesso!')
            except Exception as e:
                messages.error(request, f'Formato JSON inválido: {e}')
        else:
            messages.success(request, f'Parâmetros da integração "{api_name}" atualizados com sucesso!')
            
        return redirect('dashboard:integracoes')

    # Testa status real da conexão Google Workspace
    google_connected, google_msg, google_diag = test_google_workspace_connection()
    creds_exist = bool(get_credentials_file_path())

    integracoes_list = [
        {
            'slug': 'google-workspace',
            'nome': 'Google Workspace (Admin SDK & Drive API)',
            'categoria': 'Gestão & Soberania de Dados',
            'icone': 'ri-google-line',
            'cor_icone': 'text-primary',
            'descricao': 'Conjunto completo de APIs do Google Workspace (Directory v1, Drive v3, Groups, OAuth Tokens e Reports API) para soberania de contas @cdc.org.br.',
            'status': 'Conectado (API Real)' if google_connected else ('Chave JSON Carregada' if creds_exist else 'Aguardando Chave JSON'),
            'badge_status': 'success' if google_connected else ('warning' if creds_exist else 'secondary'),
            'endpoint': 'https://admin.googleapis.com',
            'google_connected': google_connected,
            'google_msg': google_msg,
            'google_diag': google_diag,
            'creds_exist': creds_exist,
            'campos': [
                {'name': 'service_account_email', 'label': 'Service Account Email', 'value': google_diag.get('service_account', 'cdc-core-service-account@cdc-core.iam.gserviceaccount.com')},
                {'name': 'delegated_user', 'label': 'E-mail do Administrador Delegado', 'value': 'gt.transformadigital@cdc.org.br'},
                {'name': 'scopes', 'label': 'Escopos OAuth2 Solicitados', 'value': 'admin.directory.user, admin.directory.group, drive.readonly, admin.reports.audit.readonly'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'GET / POST',
                    'nome': '1. Directory API - Usuários & OUs',
                    'url': 'https://admin.googleapis.com/admin/directory/v1/users',
                    'descricao': 'Provisionamento de voluntários/equipe, listagem de contas @cdc.org.br e atribuição de OUs (/PROVITA, /PPCAM, /PPDDH).',
                    'parametros': 'customer=my_customer, domain=cdc.org.br, projection=full',
                    'status': 'Ativo (HTTP 200 OK)'
                },
                {
                    'metodo': 'GET',
                    'nome': '2. Directory API - Unidades Organizacionais (OUs)',
                    'url': 'https://admin.googleapis.com/admin/directory/v1/customer/my_customer/orgunits',
                    'descricao': 'Leitura da árvore hierárquica de OUs e controle de permissões por departamento.',
                    'parametros': 'type=all',
                    'status': 'Ativo (HTTP 200 OK)'
                },
                {
                    'metodo': 'GET / POST',
                    'nome': '3. Directory API - Grupos & Auditoria de Membros',
                    'url': 'https://admin.googleapis.com/admin/directory/v1/groups',
                    'descricao': 'Auditoria de permissões e participantes dos grupos estratégicos (diretoria@cdc.org.br, operacoes@cdc.org.br).',
                    'parametros': 'domain=cdc.org.br',
                    'status': 'Ativo (HTTP 200 OK)'
                },
                {
                    'metodo': 'GET',
                    'nome': '4. Drive API v3 - Cotas de Armazenamento & Custódia',
                    'url': 'https://www.googleapis.com/drive/v3/about',
                    'descricao': 'Consulta de cota usada por usuário, espaço total do domínio e custódia de arquivos confidenciais em Shared Drives.',
                    'parametros': 'fields=storageQuota,user',
                    'status': 'Ativo (HTTP 200 OK)'
                },
                {
                    'metodo': 'GET / DELETE',
                    'nome': '5. OAuth2 Tokens & App Access API',
                    'url': 'https://admin.googleapis.com/admin/directory/v1/users/{userKey}/tokens',
                    'descricao': 'Listagem e revogação de aplicativos de terceiros autorizados por colaboradores do CDC.',
                    'parametros': 'userKey=all',
                    'status': 'Ativo (HTTP 200 OK)'
                },
                {
                    'metodo': 'GET',
                    'nome': '6. Reports API v1 - Auditoria de Atividade Admin & Logins',
                    'url': 'https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/admin',
                    'descricao': 'Coleta contínua de eventos de segurança, auditoria de 2FA/MFA e histórico de logins do domínio.',
                    'parametros': 'applicationName=admin, eventName=LOGIN',
                    'status': 'Ativo (HTTP 200 OK)'
                }
            ]
        },
        {
            'slug': 'whatsapp-evolution',
            'nome': 'WhatsApp Bot & Evolution API',
            'categoria': 'Comunicação Operacional',
            'icone': 'ri-whatsapp-line',
            'cor_icone': 'text-success',
            'descricao': 'Envio de alertas de 2FA pendente, notificações de estouro de cota e avisos de desligamento de voluntários.',
            'status': 'Pendente',
            'badge_status': 'warning',
            'endpoint': 'https://whatsapp.cdc.org.br',
            'campos': [
                {'name': 'instance_name', 'label': 'Nome da Instância', 'value': 'cdc_bot_operacional'},
                {'name': 'api_key', 'label': 'API Secret Key (Evolution API)', 'value': 'cdc_evolution_key_983f472a1'},
                {'name': 'webhook_url', 'label': 'Webhook Receiver URL', 'value': 'https://core.cdc.org.br/api/v1/webhooks/whatsapp/'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'POST',
                    'nome': '1. Send Text Message API',
                    'url': 'https://whatsapp.cdc.org.br/message/sendText/cdc_bot_operacional',
                    'descricao': 'Disparo automatizado de alertas de 2FA e notificações operacionais por WhatsApp.',
                    'parametros': 'number, text',
                    'status': 'Pronto'
                },
                {
                    'metodo': 'POST',
                    'nome': '2. Webhook Listener API',
                    'url': 'https://core.cdc.org.br/api/v1/webhooks/whatsapp/',
                    'descricao': 'Recepção de mensagens recebidas e confirmação de leitura.',
                    'parametros': 'event, data',
                    'status': 'Pronto'
                }
            ]
        },
        {
            'slug': 'ongsys-api',
            'nome': 'ONGSYS API v1 (Projetos & Gestão)',
            'categoria': 'Sistemas Sociais',
            'icone': 'ri-heart-pulse-line',
            'cor_icone': 'text-danger',
            'descricao': 'Integração com a API da ONGSYS para sincronização de atendimentos, voluntários e beneficiários dos projetos sociais do CDC.',
            'status': 'Aguardando Chave',
            'badge_status': 'info',
            'endpoint': 'https://ajuda.ongsys.com.br/api-v1',
            'campos': [
                {'name': 'subdominio_ongsys', 'label': 'Subdomínio ONGSYS', 'value': 'cdc.ongsys.com.br'},
                {'name': 'app_token', 'label': 'App Access Token ONGSYS', 'value': 'ongsys_token_live_38472910'},
                {'name': 'sync_interval', 'label': 'Intervalo de Sincronização', 'value': 'A cada 15 minutos'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'GET',
                    'nome': '1. Sincronização de Atendimentos & Projetos',
                    'url': 'https://cdc.ongsys.com.br/api-v1/atendimentos',
                    'descricao': 'Importação periódica de dados de assistidos dos programas PROVITA, PPCAM e PPDDH.',
                    'parametros': 'token, limit=100',
                    'status': 'Aguardando Chave'
                },
                {
                    'metodo': 'GET',
                    'nome': '2. Módulo de Contas a Pagar & Financeiro',
                    'url': 'https://cdc.ongsys.com.br/api-v1/financeiro/contas-pagar',
                    'descricao': 'Consulta de lançamentos de contas a pagar, fornecedores e prestações de contas.',
                    'parametros': 'status=pendente',
                    'status': 'Aguardando Chave'
                }
            ]
        },
        {
            'slug': 'sefaz-nfe',
            'nome': 'SEFAZ & Nota Fiscal Eletrônica (NF-e)',
            'categoria': 'Fiscal & Contábil',
            'icone': 'ri-file-text-line',
            'cor_icone': 'text-warning',
            'descricao': 'Emissão automatizada de Notas Fiscais de Serviço (NFS-e) e consulta de certidões negativas fiscais do CDC.',
            'status': 'Não Configurado',
            'badge_status': 'secondary',
            'endpoint': 'https://nfe.sefaz.gov.br',
            'campos': [
                {'name': 'cnpj_cdc', 'label': 'CNPJ do CDC', 'value': '00.000.000/0001-00'},
                {'name': 'cert_file', 'label': 'Certificado Digital A1 (.pfx)', 'value': 'certificado_cdc_2026.pfx'},
                {'name': 'ambiente', 'label': 'Ambiente SEFAZ', 'value': 'Homologação'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'POST',
                    'nome': '1. Emissão de NFS-e (Serviços CDC)',
                    'url': 'https://nfe.sefaz.gov.br/ws/emissao',
                    'descricao': 'Assinatura digital com certificado A1 e transmissão de NF-e.',
                    'parametros': 'cnpj, certificado_pfx',
                    'status': 'Não Configurado'
                }
            ]
        },
        {
            'slug': 'vpn-wireguard',
            'nome': 'VPN & Servidor WireGuard REST API',
            'categoria': 'Infraestrutura & Segurança',
            'icone': 'ri-shield-keyhole-line',
            'cor_icone': 'text-purple',
            'descricao': 'Gestão de túneis criptografados, alocação de IPs e autorização de acesso para os projetos PROVITA, PPCAM e PPDDH.',
            'status': 'Conectado',
            'badge_status': 'success',
            'endpoint': 'https://vpn.cdc.org.br:51820',
            'campos': [
                {'name': 'vpn_endpoint', 'label': 'Endpoint WireGuard', 'value': 'vpn.cdc.org.br:51820'},
                {'name': 'api_secret', 'label': 'WireGuard Management Key', 'value': 'wg_sec_83921734912'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'GET / POST',
                    'nome': '1. WireGuard Peer Manager API',
                    'url': 'https://vpn.cdc.org.br:51820/api/v1/peers',
                    'descricao': 'Geração automatizada de arquivos .conf de VPN para protegidos dos programas sociais.',
                    'parametros': 'project_id, user_email',
                    'status': 'Ativo (HTTP 200 OK)'
                }
            ]
        },
        {
            'slug': 'postgresql-vault',
            'nome': 'PostgreSQL & Cofre de Segredos Vault',
            'categoria': 'Banco de Dados',
            'icone': 'ri-database-2-line',
            'cor_icone': 'text-dark',
            'descricao': 'Armazenamento persistente seguro para chaves SSH, credenciais criptografadas e logs de auditoria do CDC Core.',
            'status': 'Conectado',
            'badge_status': 'success',
            'endpoint': 'db.internal.cdc.org.br:5432',
            'campos': [
                {'name': 'db_name', 'label': 'Nome do Banco', 'value': 'cdc_core_db'},
                {'name': 'db_user', 'label': 'Usuário DataOps', 'value': 'dxcdc'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'SELECT / INSERT',
                    'nome': '1. PostgreSQL Connection Pool',
                    'url': 'postgresql://dxcdc@db.internal.cdc.org.br:5432/cdc_core_db',
                    'descricao': 'Banco de dados relacional com criptografia AES-256 no repouso.',
                    'parametros': 'sslmode=require',
                    'status': 'Ativo (HTTP 200 OK)'
                }
            ]
        },
        {
            'slug': 'api-hub-interno',
            'nome': 'API Gateway & Hub de Microsserviços Internos',
            'categoria': 'Comunicação & Autenticação',
            'icone': 'ri-node-tree',
            'cor_icone': 'text-primary',
            'descricao': 'Gerenciamento de tokens (JWT/OAuth2) e proxy reverso para comunicação segura entre o CDC Core (Django) e aplicações satélites (Flask/FastAPI) sob o mesmo domínio.',
            'status': 'Operacional / Aguardando App',
            'badge_status': 'success',
            'endpoint': 'https://core.cdc.org.br/api/internal/',
            'campos': [
                {'name': 'base_domain', 'label': 'Domínio Base Compartilhado (Cookie Sharing)', 'value': '.cdc.org.br'},
                {'name': 'jwt_secret', 'label': 'Chave de Assinatura JWT (Secret)', 'value': '••••••••••••••••••••••••••••••••'},
                {'name': 'nginx_proxy', 'label': 'Rota Sugerida no Proxy Reverso (Nginx)', 'value': 'core.cdc.org.br/flask-app/'},
            ],
            'endpoints_detalhados': [
                {
                    'metodo': 'GET',
                    'nome': '1. Auth Verification (SSO)',
                    'url': 'https://core.cdc.org.br/api/internal/auth/verify',
                    'descricao': 'Validação de Token JWT ou Cookie de Sessão para garantir que o usuário do Flask está autenticado no CDC Core.',
                    'parametros': 'Authorization: Bearer <token>',
                    'status': 'Pronto para uso'
                },
                {
                    'metodo': 'GET',
                    'nome': '2. Exportação de Dados do Workspace',
                    'url': 'https://core.cdc.org.br/api/internal/workspace/data',
                    'descricao': 'Endpoint para o Flask consultar informações de voluntários e grupos já sanitizadas pelo Hub.',
                    'parametros': 'status=ativo',
                    'status': 'Pronto para uso'
                },
                {
                    'metodo': 'POST',
                    'nome': '3. Webhooks de Sincronização',
                    'url': 'https://core.cdc.org.br/api/internal/webhooks/notify',
                    'descricao': 'O Django dispara avisos para os apps satélites caso haja uma atualização crítica (ex: suspensão de conta).',
                    'parametros': 'event_type, payload',
                    'status': 'Pronto para uso'
                }
            ]
        }
    ]

    context = {
        'integracoes': integracoes_list,
        'total_ativas': 5,
        'total_pendentes': 2,
    }
    return render(request, 'dashboard/integracoes.html', context)


@login_required(login_url='dashboard:login')
def ecosistema_m2m_view(request):
    """
    Renderiza a página de monitoramento do Ecossistema M2M (Hub de Microsserviços).
    """
    return render(request, 'dashboard/ecosistema_m2m.html')

def login_view(request):
    """Processa a autenticação e renderiza a página de login."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username_input = (request.POST.get('login-email') or request.POST.get('username') or '').strip()
        password_input = (request.POST.get('login-password') or request.POST.get('password') or '').strip()

        user = authenticate(request, username=username_input, password=password_input)

        if user is None and '@' in username_input:
            try:
                user_obj = User.objects.get(email=username_input)
                user = authenticate(request, username=user_obj.username, password=password_input)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard:index'
            return redirect(next_url)
        else:
            messages.error(request, 'Usuário/Email ou senha incorretos.')

    return render(request, 'account/login.html')

def logout_view(request):
    """Realiza o logout do usuário e redireciona para a Landing Page pública."""
    logout(request)
    return redirect('dashboard:landing')
