from django.shortcuts import render, redirect, get_object_or_404
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
    # Consultas ao banco de dados do DataOps
    usuarios = UsuarioDataOps.objects.all()
    logs = LogAuditoria.objects.all()[:15]
    alertas_criticos = LogAuditoria.objects.filter(nivel__in=['ERROR', 'WARN'])[:5]
    
    # Casos Específicos do Documento
    adriana = UsuarioDataOps.objects.filter(email='adrianasantos@cdc.org.br').first()
    joab = UsuarioDataOps.objects.filter(email='joabsilva@cdc.org.br').first()
    joab_vinculos = MembroGrupo.objects.filter(usuario=joab) if joab else []
    paterson = UsuarioDataOps.objects.filter(email='paterson.silva@cdc.org.br').first()
    voluntarios = UsuarioDataOps.objects.filter(e_voluntario=True)

    # Estatísticas
    total_usuarios = usuarios.count()
    total_grupos = GrupoWorkspace.objects.count()
    contas_risco_cota = UsuarioDataOps.objects.filter(cota_used_gb__gte=40).count()
    contas_sem_mfa = UsuarioDataOps.objects.filter(mfa_ativo=False, status='Ativo').count()

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
            'total_usuarios': total_usuarios,
            'total_grupos': total_grupos,
            'contas_risco_cota': contas_risco_cota,
            'contas_sem_mfa': contas_sem_mfa,
        }
    }
    return render(request, 'dashboard/index.html', context)

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
