import os
import secrets
from functools import wraps
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def require_m2m_key(view_func):
    """
    Decorator que exige o cabeçalho X-API-Key válido para acesso à API M2M.
    Bloqueia requisições sem a chave ou com a chave incorreta, protegendo
    a comunicação entre o Flask e o Django Core.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Tenta pegar a chave do Header (X-API-Key)
        api_key_header = request.headers.get('X-API-Key')
        
        # 2. Pega a chave mestra verdadeira armazenada no cofre (.env)
        expected_key = os.getenv('INTERNAL_M2M_API_KEY')
        
        # 3. Se a chave mestra não foi configurada no servidor de produção, recusa por segurança
        if not expected_key:
            logger.error("ALERTA CRÍTICO: INTERNAL_M2M_API_KEY não definida no .env!")
            return JsonResponse({
                "status": "error",
                "message": "Erro interno de configuração de segurança do servidor."
            }, status=500)
            
        # 4. Compara as chaves. Se for diferente ou vazia, bloqueia na hora (Status 401)
        if not api_key_header or not secrets.compare_digest(api_key_header, expected_key):
            logger.warning(f"Tentativa de acesso não autorizada na API. IP: {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                "status": "error",
                "message": "Acesso negado. O cabeçalho X-API-Key está ausente ou inválido."
            }, status=401)
            
        # 5. Chave validada! Permite que a View principal continue a execução
        return view_func(request, *args, **kwargs)
        
    return _wrapped_view


def require_transportes_api_auth(view_func):
    """
    Proteção de Acesso para a API REST de Transportes:
    1. Permite acesso para usuários autenticados via sessão no painel do CDC Core.
    2. Permite acesso para aplicações M2M que enviem o cabeçalho 'X-API-Key' ou 'Authorization: Bearer <chave>' ou '?api_key=<chave>'.
    3. Bloqueia requisições não autorizadas com HTTP 401 Unauthorized.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Se estiver logado na sessão web do CDC Core
        if request.user and request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        # 2. Verifica token M2M nos headers ou query
        api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
        auth_header = request.headers.get('Authorization', '')
        if not api_key and auth_header.startswith('Bearer '):
            api_key = auth_header.replace('Bearer ', '').strip()

        expected_key = os.getenv('INTERNAL_M2M_API_KEY')
        if not expected_key:
            logger.error("ALERTA: INTERNAL_M2M_API_KEY não definida no .env!")
            return JsonResponse({
                "status": "error",
                "code": 500,
                "message": "Erro de segurança: Chave M2M não configurada no servidor."
            }, status=500)

        if not api_key or not secrets.compare_digest(api_key, expected_key):
            logger.warning(f"Tentativa de acesso não autorizado à API de Transportes. IP: {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                "status": "error",
                "code": 401,
                "message": "Acesso não autorizado. A API de Transportes é privada para aplicações autorizadas do ecossistema CDC. Forneça o cabeçalho 'X-API-Key' ou 'Authorization: Bearer <token>'."
            }, status=401)

        return view_func(request, *args, **kwargs)

    return _wrapped_view

