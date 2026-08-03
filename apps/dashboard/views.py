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
    """Executa simulações interativas dos 8 fluxos de automação do CDC."""
    user_exec = UsuarioDataOps.objects.filter(email='fvier@cdc.org.br').first()

    if acao == 'expandir_cota_adriana':
        adriana = UsuarioDataOps.objects.filter(email='adrianasantos@cdc.org.br').first()
        if adriana:
            adriana.cota_total_gb = 100.00
            adriana.save()
            LogAuditoria.objects.create(
                usuario_executor=user_exec,
                nivel='SUCCESS',
                acao_executada='EXPANSAO_COTA_EMERGENCIA',
                alvo_impactado='adrianasantos@cdc.org.br',
                detalhes='Cota ampliada temporariamente de 50GB para 100GB para evitar travamento de envio/recebimento de e-mails institucionais.'
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
                detalhes=f'Ex-colaborador suspenso removido com sucesso de todos os grupos institucionais ({grupos_nomes}). Brecha de privacidade corrigida.'
            )
            messages.success(request, 'Sucesso: Joab da Silva foi removido de todos os grupos de e-mail institucionais!')

    elif acao == 'auditar_mfa_geral':
        vulneraveis = UsuarioDataOps.objects.filter(mfa_ativo=False, status='Ativo')
        qtd = vulneraveis.count()
        LogAuditoria.objects.create(
            usuario_executor=user_exec,
            nivel='INFO',
            acao_executada='AUDITORIA_MFA_DOMINIO',
            alvo_impactado='Dominio @cdc.org.br',
            detalhes=f'Auditoria automatizada do SDK executada. Identificadas {qtd} contas sem Verificação em Duas Etapas (2FA/MFA).'
        )
        messages.info(request, f'Auditoria concluída: {qtd} contas identificadas sem MFA ativado.')

    elif acao == 'executar_alias_paterson':
        LogAuditoria.objects.create(
            usuario_executor=user_exec,
            nivel='SUCCESS',
            acao_executada='CONVERSAO_ALIAS',
            alvo_impactado='paterson.silva@cdc.org.br',
            detalhes='Verificação de alias: paterson.silva@cdc.org.br redirecionando com sucesso para a caixa setorial projetos@cdc.org.br.'
        )
        messages.success(request, 'Verificação concluída: Alias de Paterson Silva operando sem custos de licença!')

    return redirect('dashboard:index')

def login_view(request):
    """Processa a autenticação e renderiza a página de login."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username_input = request.POST.get('login-email', '').strip()
        password_input = request.POST.get('login-password', '').strip()

        user = authenticate(request, username=username_input, password=password_input)

        if user is None and '@' in username_input:
            try:
                user_obj = User.objects.get(email=username_input)
                user = authenticate(request, username=user_obj.username, password=password_input)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Usuário/Email ou senha incorretos.')

    return render(request, 'account/login.html')

def logout_view(request):
    """Realiza o logout do usuário e redireciona para a Landing Page pública."""
    logout(request)
    return redirect('dashboard:landing')
