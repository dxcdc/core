import base64
import re
from dataclasses import dataclass

from django.conf import settings


class OngsysCredentialsError(RuntimeError):
    pass


@dataclass(frozen=True)
class OngsysCredentials:
    username: str
    password: str
    base_url: str

    @property
    def configured(self):
        return bool(self.username and self.password and self.base_url)

    def basic_auth_header(self):
        if not self.configured:
            raise OngsysCredentialsError("Credencial OngSys v2 não configurada.")
        encoded = base64.b64encode(
            f"{self.username}:{self.password}".encode("utf-8")
        ).decode("ascii")
        return f"Basic {encoded}"


def get_ongsys_credentials():
    import os
    from pathlib import Path

    username = None
    password = None
    base_url = None

    secret_file = Path('/etc/cdc/secrets/ongsys.env')
    if secret_file.is_file():
        try:
            for line in secret_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                if key.strip() in ('ONGSYS_PASSWORD', 'ONGSYS_API_KEY') and value:
                    password = value
                elif key.strip() in ('ONGSYS_USERNAME', 'ONGSYS_CNPJ') and value:
                    username = value
                elif key.strip() in ('ONGSYS_URL_BASE', 'ONGSYS_BASE_URL') and value:
                    base_url = value
        except OSError as exc:
            raise OngsysCredentialsError(
                'Não foi possível ler o cofre de credenciais OngSys.'
            ) from exc

    if not username:
        username = os.environ.get("ONGSYS_USERNAME") or os.environ.get("ONGSYS_CNPJ") or getattr(settings, "ONGSYS_USERNAME", None) or getattr(settings, "ONGSYS_CNPJ", None)
    if not password:
        password = os.environ.get("ONGSYS_PASSWORD") or os.environ.get("ONGSYS_API_KEY") or getattr(settings, "ONGSYS_PASSWORD", None) or getattr(settings, "ONGSYS_API_KEY", None)
    if not base_url:
        base_url = os.environ.get("ONGSYS_BASE_URL") or os.environ.get("ONGSYS_URL_BASE") or getattr(settings, "ONGSYS_URL_BASE", None) or getattr(settings, "ONGSYS_BASE_URL", "https://www.ongsys.com.br/app/index.php/api/v2/")

    if not username or not password:
        raise OngsysCredentialsError("Credencial OngSys v2 não configurada no ambiente / cofre.")

    username = re.sub(r"\D", "", str(username))
    base_url = str(base_url).strip().rstrip("/") + "/"
    return OngsysCredentials(
        username=username,
        password=str(password).strip(),
        base_url=base_url if base_url != "/" else "https://www.ongsys.com.br/app/index.php/api/v2/",
    )




def get_ongsys_headers():
    credentials = get_ongsys_credentials()
    return {
        "Authorization": credentials.basic_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
