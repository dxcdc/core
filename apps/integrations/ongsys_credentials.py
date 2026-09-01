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
    import re
    from pathlib import Path
    from django.conf import settings

    username = None
    password = None
    base_url = None

    for env_file in ["/app/.env", "/root/cdc-core/.env", str(settings.BASE_DIR / ".env")]:
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in ("ONGSYS_PASSWORD", "ONGSYS_API_KEY") and v:
                            password = v
                        elif k in ("ONGSYS_USERNAME", "ONGSYS_CNPJ") and v:
                            username = v
                        elif k in ("ONGSYS_URL_BASE", "ONGSYS_BASE_URL") and v:
                            base_url = v
            except Exception:
                pass

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
    }
