import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Escopos oficiais necessários para gestão completa do CDC no Google Workspace
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.orgunit',
    'https://www.googleapis.com/auth/admin.directory.group',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/admin.reports.audit.readonly'
]

def get_credentials_file_path():
    """Retorna o caminho do arquivo de credenciais da Service Account se existir no sistema."""
    credentials_dir = os.path.join(settings.BASE_DIR, 'credentials')
    os.makedirs(credentials_dir, exist_ok=True)
    
    env_custom_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if env_custom_path and os.path.exists(env_custom_path):
        return env_custom_path

    possible_paths = [
        os.path.join(credentials_dir, 'google_service_account.json'),
        os.path.join(settings.BASE_DIR, 'google_service_account.json'),
        '/app/credentials/google_service_account.json'
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def test_google_workspace_connection(delegated_email=None):
    """
    Testa a conexão real com a Service Account do Google Workspace.
    Retorna (sucesso: bool, mensagem: str, dados_diagnostico: dict).
    """
    if not delegated_email:
        delegated_email = os.getenv('GOOGLE_DELEGATED_ADMIN_EMAIL', 'gt.transformadigital@cdc.org.br')

    creds_path = get_credentials_file_path()
    if not creds_path:
        return False, "Arquivo de chave Service Account (JSON) não encontrado. Envie a chave JSON na Central de Integrações.", {
            'status': 'Aguardando Arquivo JSON',
            'dica': 'Crie a Service Account no Google Cloud Console, ative o Admin SDK API e adicione a Delegação do Domínio Inteiro no Google Admin Console.'
        }

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=GOOGLE_SCOPES
        )

        if delegated_email:
            creds = creds.with_subject(delegated_email)

        # Testa chamada à Directory API v1 (Listagem de Usuários do Domínio)
        service = build('admin', 'directory_v1', credentials=creds)
        results = service.users().list(customer='my_customer', maxResults=10).execute()
        users = results.get('users', [])

        return True, f"Conexão real estabelecida! {len(users)} contas recuperadas do domínio.", {
            'status': 'Conectado (API Real Google Workspace)',
            'contas_encontradas': len(users),
            'delegated_email': delegated_email,
            'service_account': creds.service_account_email
        }
    except Exception as e:
        logger.error(f"Erro de autenticação no Google Workspace API: {e}")
        return False, f"Falha na conexão OAuth2: {str(e)}", {
            'status': 'Erro de Autenticação / Delegação OAuth2',
            'detalhes': str(e),
            'dica': 'Verifique se os escopos OAuth foram autorizados no Google Admin Console (Segurança > Controles de API > Delegação do Domínio Inteiro).'
        }

def fetch_google_workspace_data(delegated_email=None):
    """
    Busca dados em tempo real das APIs do Google Workspace:
    - Directory API: Users, OUs, Groups
    - Drive API: Storage Quota & Drive stats
    - Reports API: Activity logs
    """
    if not delegated_email:
        delegated_email = os.getenv('GOOGLE_DELEGATED_ADMIN_EMAIL', 'gt.transformadigital@cdc.org.br')

    creds_path = get_credentials_file_path()
    if not creds_path:
        return {'is_real': False, 'error': 'Chave JSON não configurada'}

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=GOOGLE_SCOPES
        ).with_subject(delegated_email)

        # 1. Directory API - Usuários do Domínio
        dir_service = build('admin', 'directory_v1', credentials=creds)
        users_result = dir_service.users().list(customer='my_customer', maxResults=500).execute()
        raw_users = users_result.get('users', [])

        users_list = []
        for u in raw_users:
            name = u.get('name', {}).get('fullName', u.get('primaryEmail'))
            email = u.get('primaryEmail')
            ou = u.get('orgUnitPath', '/')
            is_admin = u.get('isAdmin', False)
            suspended = u.get('suspended', False)
            status_str = 'Suspenso' if suspended else ('Ativo' if not u.get('changePasswordAtNextLogin') else 'Pendente 1º Login')
            
            users_list.append({
                'id': u.get('id'),
                'nome': name,
                'email': email,
                'cargo': 'Administrador do Domínio' if is_admin else 'Voluntário / Colaborador',
                'unidade': ou,
                'status': status_str,
                'mfa': 'Ativado (2FA)' if u.get('isEnrolledIn2Sv') else 'Não Ativado',
                'cota_usada': 'N/A'
            })

        # 2. Directory API - Unidades Organizacionais (OUs)
        try:
            ou_result = dir_service.orgunits().list(customerId='my_customer', type='all').execute()
            raw_ous = ou_result.get('organizationUnits', [])
            ous_list = [{'path': ou.get('orgUnitPath'), 'nome': ou.get('name'), 'descricao': ou.get('description', '')} for ou in raw_ous]
        except Exception as e:
            ous_list = []

        # 3. Directory API - Grupos Institucionais
        try:
            groups_result = dir_service.groups().list(customer='my_customer', maxResults=100).execute()
            raw_groups = groups_result.get('groups', [])
            groups_list = [{'nome': g.get('name'), 'email': g.get('email'), 'membros': g.get('directMembersCount', 0)} for g in raw_groups]
        except Exception as e:
            groups_list = []

        # 4. Drive API v3 - About / Storage Quota
        try:
            drive_service = build('drive', 'v3', credentials=creds)
            about_result = drive_service.about().get(fields='storageQuota').execute()
            quota = about_result.get('storageQuota', {})
            usage_bytes = int(quota.get('usage', 0))
            limit_bytes = int(quota.get('limit', 0)) if quota.get('limit') else 0
            
            usage_gb = usage_bytes / (1024 ** 3)
            limit_gb = limit_bytes / (1024 ** 3) if limit_bytes else 0
            
            quota_str = f"{usage_gb:.2f} GB de {limit_gb:.2f} GB" if limit_gb else f"{usage_gb:.2f} GB (Espaço Ilimitado)"
        except Exception as e:
            quota_str = "Consulta de Cota Ativa"

        return {
            'is_real': True,
            'users': users_list,
            'total_users': len(users_list),
            'ous': ous_list,
            'groups': groups_list,
            'drive_quota': quota_str,
            'delegated_email': delegated_email
        }
    except Exception as e:
        logger.error(f"Erro ao buscar dados reais do Google Workspace: {e}")
        return {'is_real': False, 'error': str(e)}

def save_service_account_json(json_content_or_file):
    """Salva o conteúdo da chave JSON da Service Account no diretório seguro de credenciais."""
    credentials_dir = os.path.join(settings.BASE_DIR, 'credentials')
    os.makedirs(credentials_dir, exist_ok=True)
    target_path = os.path.join(credentials_dir, 'google_service_account.json')

    if isinstance(json_content_or_file, str):
        # Valida se é um JSON válido antes de salvar
        parsed = json.loads(json_content_or_file)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2)
    else:
        # Arquivo de upload via HttpRequest
        with open(target_path, 'wb+') as destination:
            for chunk in json_content_or_file.chunks():
                destination.write(chunk)
    return target_path
