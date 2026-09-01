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
    username = os.environ.get("ONGSYS_USERNAME") or os.environ.get("ONGSYS_CNPJ") or getattr(settings, "ONGSYS_USERNAME", None) or getattr(settings, "ONGSYS_CNPJ", "03970166000129")
    username = re.sub(r"\D", "", str(username))
    password = os.environ.get("ONGSYS_PASSWORD") or os.environ.get("ONGSYS_API_KEY") or getattr(settings, "ONGSYS_PASSWORD", None) or getattr(settings, "ONGSYS_API_KEY", "fa009965195f9770db49a9111570b531")
    base_url = os.environ.get("ONGSYS_BASE_URL") or os.environ.get("ONGSYS_URL_BASE") or getattr(settings, "ONGSYS_URL_BASE", None) or getattr(settings, "ONGSYS_BASE_URL", "https://www.ongsys.com.br/app/index.php/api/v2/")
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
    }
