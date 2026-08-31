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
    username = re.sub(r"\D", "", str(settings.ONGSYS_USERNAME or ""))
    password = str(settings.ONGSYS_PASSWORD or "").strip()
    base_url = str(settings.ONGSYS_URL_BASE or "").strip().rstrip("/") + "/"
    return OngsysCredentials(
        username=username,
        password=password,
        base_url=base_url if base_url != "/" else "",
    )


def get_ongsys_headers():
    credentials = get_ongsys_credentials()
    return {
        "Authorization": credentials.basic_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
