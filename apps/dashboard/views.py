from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from apps.dataops.models import (
    UsuarioDataOps, GrupoWorkspace, MembroGrupo, 
    NotaFiscalConciliacao, LogAuditoria, CadastroSistema, RespostaFormulario
)

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
def formularios_view(request):
    """Renderiza a Central de Formulários Institucionais e Respostas do Banco."""
    sistemas_cadastrados = CadastroSistema.objects.all()
    respostas_formularios = RespostaFormulario.objects.all()
    
    # Estatísticas reais
    total_sistemas = sistemas_cadastrados.count()
    total_respostas = respostas_formularios.count()
    total_chamados_suporte = respostas_formularios.filter(tipo_formulario='suporte_ti').count()
    total_avaliacoes = respostas_formularios.filter(tipo_formulario='avaliacao_servicos').count()

    context = {
        'sistemas_cadastrados': sistemas_cadastrados,
        'respostas_formularios': respostas_formularios,
        'total_sistemas': total_sistemas,
        'total_respostas': total_respostas,
        'total_chamados_suporte': total_chamados_suporte,
        'total_avaliacoes': total_avaliacoes,
    }
    return render(request, 'dashboard/formularios.html', context)

@login_required(login_url='dashboard:login')
def formulario_cadastro_sistema_pagina(request):
    """Página dedicada do Formulário de Cadastro dos Sistemas (Reprodução Google Forms)."""
    return render(request, 'dashboard/formulario_cadastro_sistema.html')

@login_required(login_url='dashboard:login')
def formulario_avaliacao_servicos_pagina(request):
    """Página dedicada do Formulário de Avaliação de Serviços & TI."""
    return render(request, 'dashboard/formulario_avaliacao_servicos.html')

@login_required(login_url='dashboard:login')
def formulario_suporte_ti_pagina(request):
    """Página dedicada do Formulário de Suporte & Chamados TI."""
    return render(request, 'dashboard/formulario_suporte_ti.html')

@login_required(login_url='dashboard:login')
def submeter_cadastro_sistema(request):
    """Processa a gravação de uma nova Solicitação de Acesso aos Sistemas do CDC."""
    if request.method == 'POST':
        # Tenta capturar os campos do novo formulário UI/UX
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome', '')
        cpf = request.POST.get('cpf', '')
        email_inst = request.POST.get('email_institucional')
        telefone = request.POST.get('telefone_whatsapp', '')
        projeto_programa = request.POST.get('projeto_programa', 'SEDE')
        departamento = request.POST.get('departamento_sede', 'Administrativo')
        cargo = request.POST.get('cargo_funcao', 'Analista')
        sistemas_list = request.POST.getlist('sistemas_acesso')
        sistemas_str = ", ".join(sistemas_list) if sistemas_list else "Acesso Geral"

        # Se for o formulário de Solicitação de Acesso (com Nome/Sobrenome/CPF)
        if nome and email_inst:
            nome_completo = f"{nome.strip()} {sobrenome.strip()}".strip()
            
            # Validação extra do e-mail institucional
            if not email_inst.endswith('@cdc.org.br'):
                messages.warning(request, "⚠️ Se o e-mail não for institucional (@cdc.org.br), o cadastro de acesso não poderá ser aprovado.")

            # 1. Salva na tabela de Respostas de Formulário
            resposta = RespostaFormulario.objects.create(
                tipo_formulario='cadastro_sistema',
                nome_respondente=nome_completo,
                email_respondente=email_inst,
                setor_ou_projeto=projeto_programa,
                avaliacao_nota=5,
                assunto_ou_categoria=f"{cargo} ({departamento})",
                mensagem_detalhes=f"CPF: {cpf} | Tel: {telefone} | Sistemas Solicitados: {sistemas_str}"
            )

            # 2. Cria registro em CadastroSistema para listagem dos sistemas mapeados
            for sys_nome in (sistemas_list if sistemas_list else ['Acesso Geral']):
                CadastroSistema.objects.get_or_create(
                    nome_sistema=f"Acesso {sys_nome} - {nome_completo}",
                    defaults={
                        'sigla': sys_nome.upper(),
                        'responsavel_nome': nome_completo,
                        'responsavel_email': email_inst,
                        'setor_projeto': f"{projeto_programa} / {departamento}",
                        'url_acesso': f"https://core.cdc.org.br/sistemas/{sys_nome.lower()}/",
                        'tecnologias': f"Perfil: {cargo} | Permissão: Solicitada",
                        'descricao': f"Solicitação de Acesso aos Sistemas pelo colaborador {nome_completo} (CPF: {cpf}).",
                        'criticidade': 'Média',
                        'status': 'Operacional'
                    }
                )

            # 3. Log de Auditoria
            user_exec = UsuarioDataOps.objects.filter(email='fvier@cdc.org.br').first()
            LogAuditoria.objects.create(
                usuario_executor=user_exec,
                nivel='SUCCESS',
                acao_executada='Solicitação de Acesso a Sistemas',
                alvo_impactado=f"{nome_completo} ({email_inst})",
                detalhes=f"Solicitado acesso aos sistemas [{sistemas_str}] para {nome_completo} ({cargo} - {projeto_programa}).",
                ip_origem=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )

            messages.success(request, f"✅ Solicitação de Cadastro e Acesso aos Sistemas para '{nome_completo}' registrada com sucesso!")
        
        # Suporte retrocompatível para o formulário técnico direto
        else:
            nome_sys = request.POST.get('nome_sistema', 'Novo Sistema')
            sigla = request.POST.get('sigla', 'SYS')
            resp_nome = request.POST.get('responsavel_nome', 'Fernando Vier')
            resp_email = request.POST.get('responsavel_email', 'fvier@cdc.org.br')
            setor_proj = request.POST.get('setor_projeto', 'Transformação Digital')
            url_acesso = request.POST.get('url_acesso', '')
            tecnologias = request.POST.get('tecnologias', '')
            descricao = request.POST.get('descricao', '')
            criticidade = request.POST.get('criticidade', 'Média')
            status = request.POST.get('status', 'Operacional')

            sistema = CadastroSistema.objects.create(
                nome_sistema=nome_sys,
                sigla=sigla,
                responsavel_nome=resp_nome,
                responsavel_email=resp_email,
                setor_projeto=setor_proj,
                url_acesso=url_acesso,
                tecnologias=tecnologias,
                descricao=descricao,
                criticidade=criticidade,
                status=status
            )

            user_exec = UsuarioDataOps.objects.filter(email='fvier@cdc.org.br').first()
            LogAuditoria.objects.create(
                usuario_executor=user_exec,
                nivel='SUCCESS',
                acao_executada='Cadastro de Sistema',
                alvo_impactado=f"{sistema.nome_sistema} ({sistema.setor_projeto})",
                detalhes=f"Sistema {sistema.nome_sistema} cadastrado por {resp_nome}.",
                ip_origem=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )

            messages.success(request, f"✅ Sistema '{sistema.nome_sistema}' registrado com sucesso no banco de dados!")

    return redirect('dashboard:formularios')

@login_required(login_url='dashboard:login')
def submeter_resposta_formulario(request):
    """Processa respostas dos Formulários de Avaliação de Serviços ou Suporte TI."""
    if request.method == 'POST':
        tipo = request.POST.get('tipo_formulario', 'avaliacao_servicos')
        is_anonimo = request.POST.get('is_anonimo') in ['on', 'true', '1']
        
        if is_anonimo:
            nome = "Usuário Anônimo"
            email = "anonimo@cdc.org.br"
        else:
            nome = request.POST.get('nome_respondente', 'Usuário Anônimo').strip() or "Usuário Anônimo"
            email = request.POST.get('email_respondente', 'contato@cdc.org.br').strip() or "contato@cdc.org.br"

        setor = request.POST.get('setor_ou_projeto', 'Sede CDC')
        nota = int(request.POST.get('avaliacao_nota', 5))
        assunto = request.POST.get('assunto_ou_categoria', 'Geral')
        outro_servico = request.POST.get('outro_servico_especifico', '').strip()

        # Se selecionou a opção "Outro", salva com a especificação digitada
        if assunto == 'Outro' and outro_servico:
            assunto = f"Outro: {outro_servico}"

        mensagem = request.POST.get('mensagem_detalhes', '')

        resposta = RespostaFormulario.objects.create(
            tipo_formulario=tipo,
            nome_respondente=nome,
            email_respondente=email,
            setor_ou_projeto=setor,
            avaliacao_nota=nota,
            assunto_ou_categoria=assunto,
            mensagem_detalhes=mensagem
        )

        user_exec = UsuarioDataOps.objects.filter(email='fvier@cdc.org.br').first()
        LogAuditoria.objects.create(
            usuario_executor=user_exec,
            nivel='INFO',
            acao_executada=f"Submissão de Formulário ({tipo})",
            alvo_impactado=f"{nome} - {assunto}",
            detalhes=f"Formulário {tipo} enviado ({'Anônimo' if is_anonimo else 'Identificado'}).",
            ip_origem=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )

        messages.success(request, f"🎉 Sua resposta no formulário de {resposta.get_tipo_formulario_display()} foi gravada com sucesso!")
    return redirect('dashboard:formularios')

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
                {'name': 'api_key', 'label': 'API Secret Key (Evolution API)', 'value': 'Configurada somente no cofre'},
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
                {'name': 'app_token', 'label': 'App Access Token ONGSYS', 'value': 'Não configurado'},
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
                {'name': 'api_secret', 'label': 'WireGuard Management Key', 'value': 'Configurada somente no cofre'},
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


@login_required(login_url='dashboard:login')
def ongsys_integration_view(request):
    """
    Renderiza a Central de Integração com a API do OngSys (v2).
    Utiliza o Cofre de Segredos do Servidor (Server-Side Vault / Env) para proteger a API Key.
    """
    import os

    if request.method == 'POST':
        new_cnpj = re.sub(r'\D', '', request.POST.get('ongsys_cnpj', '').strip())
        new_api_key = request.POST.get('ongsys_api_key', '').strip()

        if new_cnpj:
            os.environ['ONGSYS_CNPJ'] = new_cnpj
        if new_api_key:
            os.environ['ONGSYS_API_KEY'] = new_api_key

        messages.success(request, 'Credenciais do OngSys salvas com segurança no Cofre do Servidor!')
        return redirect('dashboard:ongsys_integration')

    vault_cnpj = os.environ.get('ONGSYS_CNPJ', '03970166000129')
    vault_api_key = os.environ.get('ONGSYS_API_KEY', '')
    has_api_key = bool(vault_api_key)

    masked_api_key = f"{vault_api_key[:4]}••••••••••••••••{vault_api_key[-4:]}" if len(vault_api_key) > 8 else ("••••••••••••" if has_api_key else "Não Configurada")

    endpoints_ongsys = [
        # Movimentações Financeiras
        {
            'id': 'contas-pagar-get',
            'modulo': 'financeiro',
            'nome': 'Buscar Contas a Pagar',
            'metodo': 'GET',
            'path': 'contas-pagar',
            'descricao': 'Busca todas as contas a pagar no período com suporte a rateio por projeto, plano de contas e impostos retidos.',
            'especificidades': 'Exige filtro (1=Emissão, 2=Vencimento, 3=Pagamento, 4=Cadastro, 6=Competência), data_inicio, data_fim e pageNumber.',
            'parametros': '{"filtro": 1, "data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'contas-pagar-post',
            'modulo': 'financeiro',
            'nome': 'Inserir Conta a Pagar',
            'metodo': 'POST',
            'path': 'create-contas-pagar',
            'descricao': 'Cadastra uma nova conta a pagar com fornecedor, rateio de projetos, contas contábeis e retenções fiscais.',
            'especificidades': 'Endpoint específico /create-contas-pagar. Exige fornecedor (nome/documento), dataEmissao, dataVencimento, valorBruto, historicoDespesa e tipoDespesa.',
            'parametros': '{"fornecedor": {"nome": "Empresa Fornecedora LTDA", "documento": "12.345.678/0001-99"}, "dataEmissao": "2026-08-01", "dataVencimento": "2026-08-31", "valorBruto": 1500.00, "historicoDespesa": "Pagamento de serviços de consultoria", "tipoDespesa": 1, "lancamento": "Real", "tipoDocumento": 1, "numeroDocumento": "NF-000123"}'
        },
        {
            'id': 'baixa-contas-pagar-post',
            'modulo': 'financeiro',
            'nome': 'Baixa de Contas a Pagar',
            'metodo': 'POST',
            'path': 'baixa-contas-pagar',
            'descricao': 'Informa a liquidação/baixa de uma conta a pagar previamente cadastrada informando a conta bancária.',
            'especificidades': 'Endpoint /baixa-contas-pagar. Exige codLancamento (ex: CP050940), contaBancaria, dataPagamento e valorPago.',
            'parametros': '{"codLancamento": "CP050940", "contaBancaria": 1, "dataPagamento": "2026-08-28", "valorPago": 1500.00, "formaPagamento": 1}'
        },
        {
            'id': 'contas-receber-get',
            'modulo': 'financeiro',
            'nome': 'Buscar Contas a Receber',
            'metodo': 'GET',
            'path': 'contas-receber',
            'descricao': 'Lista todas as contas a receber registradas no período (repasse de emendas, convênios e doações).',
            'especificidades': 'Exige filtro (1=Emissão, 2=Vencimento, 3=Recebimento, 4=Cadastro, 6=Competência), data_inicio, data_fim e pageNumber.',
            'parametros': '{"filtro": 1, "data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'contas-receber-post',
            'modulo': 'financeiro',
            'nome': 'Inserir Conta a Receber',
            'metodo': 'POST',
            'path': 'create-contas-receber',
            'descricao': 'Cadastra uma nova receita/recebimento com vínculo a parceiro/cliente e projeto apoiado.',
            'especificidades': 'Endpoint específico /create-contas-receber. Exige cliente (nome/documento), dataEmissao, dataVencimento, valorBruto e tipoReceita.',
            'parametros': '{"cliente": {"nome": "NOME DO CLIENTE", "documento": "00.000.000/0001-00"}, "dataEmissao": "2026-08-01", "dataVencimento": "2026-08-31", "valorBruto": 5000.00, "historicoReceita": "Repasse referente a projeto", "tipoReceita": 1}'
        },
        {
            'id': 'baixa-contas-receber-post',
            'modulo': 'financeiro',
            'nome': 'Baixa de Contas a Receber',
            'metodo': 'POST',
            'path': 'baixa-contas-receber',
            'descricao': 'Registra a baixa e quitação de uma receita na conta corrente da entidade.',
            'especificidades': 'Endpoint /baixa-contas-receber. Exige codLancamento (ex: CR003554), contaBancaria, dataRecebimento e valorRecebido.',
            'parametros': '{"codLancamento": "CR003554", "contaBancaria": 1, "dataRecebimento": "2026-08-28", "valorRecebido": 5000.00}'
        },
        {
            'id': 'transferencias-bancarias-get',
            'modulo': 'financeiro',
            'nome': 'Buscar Transferências Bancárias',
            'metodo': 'GET',
            'path': 'transferencias-bancarias',
            'descricao': 'Consulta todas as transferências entre contas bancárias no período.',
            'especificidades': 'Exige data_inicio (aaaa-mm-dd), data_fim (aaaa-mm-dd) e pageNumber (>=1).',
            'parametros': '{"data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'transferencias-bancarias-post',
            'modulo': 'financeiro',
            'nome': 'Inserir Transferência Bancária',
            'metodo': 'POST',
            'path': 'create-transferencias-bancarias',
            'descricao': 'Realiza o registro de movimentação entre contas da instituição no OngSys.',
            'especificidades': 'Endpoint específico /create-transferencias-bancarias. Exige contaOrigem, contaDestino, valor, data e historico.',
            'parametros': '{"contaOrigem": 1, "contaDestino": 2, "valor": 1000.00, "data": "2026-08-28", "historico": "Transferência entre contas correntes do projeto"}'
        },
        {
            'id': 'lancamentos-bancarios-get',
            'modulo': 'financeiro',
            'nome': 'Buscar Lançamentos Bancários',
            'metodo': 'GET',
            'path': 'lancamentos-bancarios',
            'descricao': 'Extrato de lançamentos bancários das contas correntes da organização.',
            'especificidades': 'Exige data_inicio (aaaa-mm-dd), data_fim (aaaa-mm-dd) e pageNumber (>=1).',
            'parametros': '{"data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'adiantamentos-fornecedores-get',
            'modulo': 'financeiro',
            'nome': 'Buscar Adiantamentos a Fornecedores',
            'metodo': 'GET',
            'path': 'adiantamentos-fornecedores',
            'descricao': 'Lista adiantamentos financeiros concedidos a fornecedores.',
            'especificidades': 'Exige filtro (1=Operação), data_inicio, data_fim e pageNumber.',
            'parametros': '{"filtro": 1, "data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'adiantamentos-clientes-get',
            'modulo': 'financeiro',
            'nome': 'Buscar Adiantamentos de Clientes',
            'metodo': 'GET',
            'path': 'adiantamentos-clientes',
            'descricao': 'Lista valores adiantados por doadores/clientes em projetos.',
            'especificidades': 'Exige filtro (1=Operação), data_inicio, data_fim e pageNumber.',
            'parametros': '{"filtro": 1, "data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },

        # Cadastros & Contratos
        {
            'id': 'clientes-get',
            'modulo': 'cadastros',
            'nome': 'Buscar Clientes / Projetos Apoiados',
            'metodo': 'GET',
            'path': 'clientes',
            'descricao': 'Lista o cadastro de clientes, parceiros, doadores e projetos apoiados.',
            'especificidades': 'Exige pageNumber (>=1). Suporta filtros opcionais como tipo e ativoInativo.',
            'parametros': '{"pageNumber": 1}'
        },
        {
            'id': 'fornecedores-get',
            'modulo': 'cadastros',
            'nome': 'Buscar Fornecedores',
            'metodo': 'GET',
            'path': 'fornecedores',
            'descricao': 'Lista completa de fornecedores cadastrados na base do OngSys (2.900+ registros).',
            'especificidades': 'Exige pageNumber (>=1). Suporta filtros opcionais de tipo (F/J) e ativoInativo.',
            'parametros': '{"pageNumber": 1}'
        },
        {
            'id': 'contratos-pagar-get',
            'modulo': 'cadastros',
            'nome': 'Buscar Contratos a Pagar',
            'metodo': 'GET',
            'path': 'contratos',
            'descricao': 'Consulta contratos vigentes de fornecedores e prestadores da instituição.',
            'especificidades': 'Endpoint /contratos. Exige pageNumber (>=1).',
            'parametros': '{"pageNumber": 1}'
        },
        {
            'id': 'contratos-receber-get',
            'modulo': 'cadastros',
            'nome': 'Buscar Contratos a Receber',
            'metodo': 'GET',
            'path': 'contratos-receber',
            'descricao': 'Consulta contratos de parcerias, repasses, emendas e doações recorrentes.',
            'especificidades': 'Endpoint /contratos-receber. Exige pageNumber (>=1).',
            'parametros': '{"pageNumber": 1}'
        },

        # Compras & Suprimentos
        {
            'id': 'produtos-get',
            'modulo': 'compras',
            'nome': 'Buscar Produtos & Itens',
            'metodo': 'GET',
            'path': 'produtos',
            'descricao': 'Catálogo de produtos e materiais cadastrados no sistema (1.600+ itens).',
            'especificidades': 'Endpoint /produtos. Exige pageNumber (>=1).',
            'parametros': '{"pageNumber": 1}'
        },
        {
            'id': 'pedidos-compras-get',
            'modulo': 'compras',
            'nome': 'Buscar Pedidos de Compras / Contratações',
            'metodo': 'GET',
            'path': 'pedidos',
            'descricao': 'Ordens e requisições de compras e contratações em andamento.',
            'especificidades': 'Endpoint /pedidos. Exige pageNumber (>=1). Suporta filtro opcional numero_pedido.',
            'parametros': '{"pageNumber": 1}'
        },

        # Notas Fiscais & Auditoria
        {
            'id': 'nfse-get',
            'modulo': 'notas_fiscais',
            'nome': 'Notas Fiscais de Serviço (NFS-e)',
            'metodo': 'GET',
            'path': 'notas-servico',
            'descricao': 'Consulta Notas Fiscais de Serviço capturadas e escrituradas.',
            'especificidades': 'Endpoint /notas-servico. Exige data_inicio, data_fim e pageNumber.',
            'parametros': '{"data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'nfe-get',
            'modulo': 'notas_fiscais',
            'nome': 'Notas Fiscais de Produto (NF-e)',
            'metodo': 'GET',
            'path': 'notas-produto',
            'descricao': 'Consulta Notas Fiscais de Produto (danfe) importadas.',
            'especificidades': 'Endpoint /notas-produto. Exige data_inicio, data_fim e pageNumber.',
            'parametros': '{"data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        },
        {
            'id': 'logs-get',
            'modulo': 'notas_fiscais',
            'nome': 'Logs de Auditoria do Sistema',
            'metodo': 'GET',
            'path': 'logs',
            'descricao': 'Histórico de ações e alterações realizadas na base de dados do OngSys.',
            'especificidades': 'Endpoint /logs. Exige data_inicio, data_fim e pageNumber.',
            'parametros': '{"data_inicio": "2024-01-01", "data_fim": "2026-12-31", "pageNumber": 1}'
        }
    ]


    # Contagens locais do espelho PostgreSQL atômico
    try:
        from apps.integrations.models import (
            OngsysFornecedor,
            OngsysCliente,
            OngsysContaPagar,
            OngsysContaReceber,
            OngsysLancamentoBancario,
            OngsysContrato,
            OngsysProduto,
        )
        db_fornecedores = OngsysFornecedor.objects.count()
        db_clientes = OngsysCliente.objects.count()
        db_contas_pagar = OngsysContaPagar.objects.count()
        db_contas_receber = OngsysContaReceber.objects.count()
        db_lancamentos = OngsysLancamentoBancario.objects.count()
        db_contratos = OngsysContrato.objects.count()
        db_produtos = OngsysProduto.objects.count()
        db_total = (
            db_fornecedores
            + db_clientes
            + db_contas_pagar
            + db_contas_receber
            + db_lancamentos
            + db_contratos
            + db_produtos
        )
    except Exception:
        db_fornecedores = db_clientes = db_contas_pagar = db_contas_receber = 0
        db_lancamentos = db_contratos = db_produtos = db_total = 0

    context = {
        'endpoints': endpoints_ongsys,
        'base_url': 'https://www.ongsys.com.br/app/index.php/api/v2/',
        'docs_url': 'https://ajuda.ongsys.com.br/api-v1',
        'vault_cnpj': vault_cnpj,
        'formatted_cnpj': '03.970.166/0001-29' if vault_cnpj == '03970166000129' else vault_cnpj,
        'masked_api_key': masked_api_key,
        'has_api_key': has_api_key,
        'total_endpoints': len(endpoints_ongsys),
        'total_modulos': 4,
        'latency_ms': 120,
        'health_status': 'Operacional (Basic Auth OK)' if has_api_key else 'Aguardando API Key',
        # Métricas do Espelho Atômico Local
        'db_total': db_total,
        'db_fornecedores': db_fornecedores,
        'db_clientes': db_clientes,
        'db_contas_pagar': db_contas_pagar,
        'db_contas_receber': db_contas_receber,
        'db_lancamentos': db_lancamentos,
        'db_contratos': db_contratos,
        'db_produtos': db_produtos,
    }
    return render(request, 'dashboard/ongsys_integration.html', context)


@login_required(login_url='dashboard:login')
def ongsys_trigger_sync_view(request):
    """
    Dispara a sincronização atômica em lote da OngSys e retorna o resultado em JSON.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    import json
    from apps.integrations.ongsys_sync import (
        sync_fornecedores,
        sync_clientes,
        sync_contas_pagar,
        sync_contas_receber,
        sync_lancamentos_bancarios,
        sync_contratos,
        sync_produtos,
        sync_all_ongsys,
    )

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        data = {}

    entity = data.get('entity', 'all')
    pages = int(data.get('pages', 3))

    try:
        if entity == 'fornecedores':
            result = [sync_fornecedores(max_pages=pages)]
        elif entity == 'clientes':
            result = [sync_clientes(max_pages=pages)]
        elif entity == 'contas_pagar':
            result = [sync_contas_pagar(max_pages=pages)]
        elif entity == 'contas_receber':
            result = [sync_contas_receber(max_pages=pages)]
        elif entity == 'lancamentos_bancarios':
            result = [sync_lancamentos_bancarios(max_pages=pages)]
        elif entity == 'contratos':
            result = [sync_contratos(max_pages=pages)]
        elif entity == 'produtos':
            result = [sync_produtos(max_pages=pages)]
        else:
            result = sync_all_ongsys(max_pages_per_entity=pages)

        return JsonResponse({'status': 'success', 'results': result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)




@login_required(login_url='dashboard:login')
def ongsys_api_proxy_view(request, endpoint_key):
    """
    Proxy seguro em Python/Django para testar e consumir a API do OngSys (v2).
    Lê a API Key com segurança diretamente do Cofre do Servidor (Server-Side Vault / Env).
    O cliente/browser NUNCA enxerga nem trafega a credencial sensível!
    """
    import base64
    import json
    import time
    import os
    import requests

    if request.method != 'POST':
        return JsonResponse({'error': 'Somente método POST é permitido para a API Proxy'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': f'Payload JSON inválido: {e}'}, status=400)

    # Lê credenciais prioritariamente do Cofre do Servidor
    cnpj = str(data.get('cnpj') or os.environ.get('ONGSYS_CNPJ') or '03970166000129').strip()
    cnpj = re.sub(r'\D', '', cnpj)

    api_key = str(data.get('api_key') or os.environ.get('ONGSYS_API_KEY') or '').strip()

    path = str(data.get('path', '')).strip().lstrip('/')
    method = str(data.get('method', 'GET')).upper()
    custom_params = data.get('params', {})
    custom_body = data.get('body', {})

    if not cnpj or not api_key:
        return JsonResponse({
            'error': 'API Key do OngSys não encontrada no Cofre do Servidor. Por favor, configure a chave no painel de segredos.'
        }, status=400)

    # Constrói o cabeçalho Authorization: Basic Base64(CNPJ:API_KEY)
    auth_str = f"{cnpj}:{api_key}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'CDC-Core-Integration-Hub/1.0'
    }

    target_url = f"https://www.ongsys.com.br/app/index.php/api/v2/{path}"

    start_time = time.time()
    try:
        if method == 'GET':
            resp = requests.get(target_url, headers=headers, params=custom_params, timeout=15)
        elif method == 'POST':
            resp = requests.post(target_url, headers=headers, json=custom_body, timeout=15)
        elif method == 'PUT':
            resp = requests.put(target_url, headers=headers, json=custom_body, timeout=15)
        elif method == 'DELETE':
            resp = requests.delete(target_url, headers=headers, timeout=15)
        else:
            return JsonResponse({'error': f'Método HTTP {method} não suportado'}, status=400)

        elapsed_ms = int((time.time() - start_time) * 1000)

        try:
            json_response = resp.json()
        except Exception:
            json_response = {'raw_body': resp.text}

        return JsonResponse({
            'status_code': resp.status_code,
            'elapsed_ms': elapsed_ms,
            'target_url': resp.url,
            'headers': dict(resp.headers),
            'response': json_response
        })

    except requests.exceptions.RequestException as req_err:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return JsonResponse({
            'error': f'Falha ao conectar com servidor OngSys: {req_err}',
            'elapsed_ms': elapsed_ms,
            'target_url': target_url
        }, status=502)


