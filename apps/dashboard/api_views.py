from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .api_auth import require_m2m_key

@require_GET
@require_m2m_key
def auth_verify_view(request):
    """
    Endpoint 1: Validação de Auth (SSO / Handshake).
    Se o Flask conseguir chamar isso sem erro 401, significa que a 
    chave dele é válida. Devolvemos um JSON afirmativo.
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
    Endpoint 2: Dados do Workspace.
    Fornece ao app satélite (Flask) um resumo sanitizado dos dados do Google Workspace
    que o CDC Core já processou, evitando que o Flask tenha que falar com o Google direto.
    """
    # Exemplo estático simulando os dados mastigados que já temos na Dashboard
    # No futuro, podemos plugar isso direto nas funções do `google_service.py`
    payload = {
        "status": "success",
        "data": {
            "resumo": {
                "contas_ativas": 142,
                "contas_suspensas": 12,
                "contas_sem_mfa": 3,
                "aliases_gratuitos": 45
            },
            "alertas": [
                "Cota de armazenamento no Google Drive atingiu 85%.",
                "3 usuários críticos sem Autenticação de Dois Fatores (MFA)."
            ]
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
