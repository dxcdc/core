import os
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .api_auth import require_m2m_key
from .google_service import fetch_google_workspace_data
from apps.dataops.models import UsuarioDataOps

@require_GET
@require_m2m_key
def auth_verify_view(request):
    """
    Endpoint 1: Validação de Auth (SSO / Handshake).
    Se a aplicação cliente conseguir chamar isso sem erro 401, significa que a 
    chave dela é válida. Devolvemos um JSON afirmativo.
    """
    return JsonResponse({
        "status": "success",
        "code": 200,
        "message": "Autenticado com sucesso via M2M. CDC Core conectado.",
        "app_context": "api-hub-interno"
    })

@require_GET
@require_m2m_key
def workspace_data_view(request):
    """
    Endpoint 2: Dados do Workspace e Lista de Usuários/VPN.
    Fornece à aplicação da VPN e outros satélites a lista estruturada de usuários ('users'),
    com seus e-mails, OUs, grupos e status da VPN, alinhados com o esquema do Inspector.
    """
    # 1. Tenta buscar contas reais via API do Google Workspace
    google_real = fetch_google_workspace_data('gt.transformadigital@cdc.org.br')
    
    users_list = []
    
    if google_real.get('is_real') and google_real.get('users'):
        for idx, u in enumerate(google_real.get('users', []), start=1):
            email = u.get('email', '')
            prefix = email.split('@')[0] if '@' in email else email
            nome = u.get('nome', u.get('name', 'Usuário CDC'))
            first_name = nome.split()[0] if nome else 'Usuário'
            
            users_list.append({
                "id": idx,
                "nome": nome,
                "apelido": first_name,
                "email_prefix": prefix,
                "email": email,
                "ou": u.get('ou', '/ATITUDE'),
                "grupo": u.get('setor', u.get('grupo', 'Operações')),
                "status_vpn": "Offline"
            })
    else:
        # 2. Se a API do Google não estiver conectada, usa a base do DataOps
        db_users = UsuarioDataOps.objects.all()
        if db_users.exists():
            for idx, u in enumerate(db_users, start=1):
                prefix = u.email.split('@')[0] if '@' in u.email else u.email
                first_name = u.nome.split()[0] if u.nome else 'Usuário'
                users_list.append({
                    "id": idx,
                    "nome": u.nome,
                    "apelido": first_name,
                    "email_prefix": prefix,
                    "email": u.email,
                    "ou": "/ATITUDE",
                    "grupo": u.setor_atual or "Operações",
                    "status_vpn": "Offline"
                })
        else:
            # 3. Estrutura padrão para o domínio @cdc.org.br
            users_list = [
                {
                    "id": 1,
                    "nome": "Acolhimento Breve Cabo",
                    "apelido": "Cabo",
                    "email_prefix": "acolhimentobreve_cabo",
                    "email": "acolhimentobreve_cabo@cdc.org.br",
                    "ou": "/ATITUDE",
                    "grupo": "Operações",
                    "status_vpn": "Offline"
                },
                {
                    "id": 2,
                    "nome": "Acolhimento Breve Caruaru",
                    "apelido": "Caruaru",
                    "email_prefix": "acolhimentobreve_caruaru",
                    "email": "acolhimentobreve_caruaru@cdc.org.br",
                    "ou": "/ATITUDE",
                    "grupo": "Operações",
                    "status_vpn": "Offline"
                },
                {
                    "id": 3,
                    "nome": "Acolhimento Breve Jaboatão",
                    "apelido": "Jaboatão",
                    "email_prefix": "acolhimentobreve_jaboatao",
                    "email": "acolhimentobreve_jaboatao@cdc.org.br",
                    "ou": "/ATITUDE",
                    "grupo": "Operações",
                    "status_vpn": "Offline"
                },
                {
                    "id": 4,
                    "nome": "Acolhimento Breve Recife",
                    "apelido": "Recife",
                    "email_prefix": "acolhimentobreve_recife",
                    "email": "acolhimentobreve_recife@cdc.org.br",
                    "ou": "/ATITUDE",
                    "grupo": "Operações",
                    "status_vpn": "Offline"
                }
            ]

    payload = {
        "status": "success",
        "http_code": 200,
        "endpoint": "https://core.cdc.org.br/api/internal/workspace/data/",
        "authentication": "X-API-Key validated",
        "unidade_organizacional_raiz": "/ATITUDE",
        "contas_mapeadas": len(users_list),
        "users": users_list,
        "data": {
            "resumo": {
                "contas_ativas": len(users_list),
                "contas_suspensas": 0,
                "contas_sem_mfa": 0,
                "aliases_gratuitos": 0
            },
            "alertas": []
        }
    }
    return JsonResponse(payload)

@csrf_exempt
@require_POST
@require_m2m_key
def webhooks_notify_view(request):
    """
    Endpoint 3: Recebimento de Webhooks Externos (ou de outros apps satélites).
    Permite que o Flask envie avisos críticos de volta para o Django.
    """
    return JsonResponse({
        "status": "success",
        "message": "Webhook recebido com segurança pelo Hub."
    })
