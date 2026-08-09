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
    
    possible_paths = [
        os.path.join(credentials_dir, 'google_service_account.json'),
        os.path.join(settings.BASE_DIR, 'google_service_account.json'),
        '/app/credentials/google_service_account.json'
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def test_google_workspace_connection(delegated_email='dxcdc@cdc.org.br'):
    """
    Testa a conexão real com a Service Account do Google Workspace.
    Retorna (sucesso: bool, mensagem: str, dados_diagnostico: dict).
    """
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
