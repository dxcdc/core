import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class NextERPError(Exception):
    code = "nexterp_error"


class NextERPConfigurationError(NextERPError):
    code = "configuration_error"


class NextERPAuthenticationError(NextERPError):
    code = "authentication_error"


class NextERPAuthorizationError(NextERPError):
    code = "authorization_error"


class NextERPRateLimitError(NextERPError):
    code = "rate_limit_error"


class NextERPServerError(NextERPError):
    code = "server_error"


class NextERPContractError(NextERPError):
    code = "contract_error"


@dataclass(frozen=True)
class DatasetPage:
    records: list[dict]
    next_cursor: str
    has_more: bool
    contract_version: str
    checkpoint: datetime


class NextERPAnalyticsClient:
    dataset_path = "/api/method/cdc_theme.api.get_cdc_analytics_dataset"
    catalog_path = "/api/method/cdc_theme.api.get_cdc_analytics_catalog"
    ongsys_mappings_path = (
        "/api/method/cdc_theme.api.get_ongsys_warehouse_mappings_for_extractor"
    )

    def __init__(
        self,
        *,
        base_url=None,
        api_key=None,
        api_secret=None,
        connect_timeout=None,
        read_timeout=None,
        max_retries=None,
        session=None,
        sleeper=time.sleep,
    ):
        self.base_url = (base_url if base_url is not None else settings.NEXTERP_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.NEXTERP_API_KEY
        self.api_secret = api_secret if api_secret is not None else settings.NEXTERP_API_SECRET
        self.connect_timeout = connect_timeout or settings.NEXTERP_CONNECT_TIMEOUT
        self.read_timeout = read_timeout or settings.NEXTERP_READ_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else settings.NEXTERP_MAX_RETRIES
        self.session = session or requests.Session()
        self.sleeper = sleeper
        self.last_attempts = 0
        if not self.base_url or not self.api_key or not self.api_secret:
            raise NextERPConfigurationError("Configuração M2M do NextERP incompleta.")

    def fetch_dataset_page(self, dataset, *, cursor="", modified_since=None, correlation_id=None):
        params = {"dataset": dataset}
        if cursor:
            params["cursor"] = cursor
        if modified_since:
            params["modified_since"] = modified_since.isoformat()
        payload = self._get(self.dataset_path, params, correlation_id or uuid.uuid4())
        return self._validate_page(payload)

    def fetch_catalog(self, *, correlation_id=None):
        payload = self._get(self.catalog_path, {}, correlation_id or uuid.uuid4())
        return self._validate_catalog(payload)

    def fetch_ongsys_warehouse_mappings(self, *, correlation_id=None):
        payload = self._get(self.ongsys_mappings_path, {}, correlation_id or uuid.uuid4())
        return self._validate_ongsys_warehouse_mappings(payload)

    def _get(self, path, params, correlation_id):
        headers = {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Accept": "application/json",
            "X-Correlation-ID": str(correlation_id),
        }
        url = f"{self.base_url}{path}"
        retryable_statuses = {429, 500, 502, 503, 504}
        for attempt in range(1, self.max_retries + 2):
            self.last_attempts = attempt
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=(self.connect_timeout, self.read_timeout),
                )
            except requests.RequestException as exc:
                if attempt > self.max_retries:
                    raise NextERPServerError("Falha de comunicação com o NextERP.") from exc
                self._backoff(attempt, correlation_id)
                continue

            if response.status_code == 401:
                raise NextERPAuthenticationError("Credencial M2M do NextERP recusada.")
            if response.status_code == 403:
                raise NextERPAuthorizationError("Usuário M2M sem permissão para o recurso solicitado.")
            if response.status_code == 429 and attempt > self.max_retries:
                raise NextERPRateLimitError("Limite de requisições do NextERP excedido.")
            if response.status_code >= 500 and attempt > self.max_retries:
                raise NextERPServerError("NextERP indisponível após as retentativas.")
            if response.status_code in retryable_statuses:
                self._backoff(attempt, correlation_id)
                continue
            if response.status_code >= 400:
                raise NextERPError(f"NextERP recusou a requisição (HTTP {response.status_code}).")
            try:
                return response.json()
            except ValueError as exc:
                raise NextERPContractError("NextERP retornou JSON inválido.") from exc
        raise NextERPServerError("Falha inesperada ao consultar o NextERP.")

    def _backoff(self, attempt, correlation_id):
        logger.warning(
            "NextERP temporariamente indisponível; nova tentativa",
            extra={"correlation_id": str(correlation_id), "attempt": attempt},
        )
        self.sleeper(min(2 ** (attempt - 1), 30))

    @staticmethod
    def _validate_page(payload):
        if not isinstance(payload, dict):
            raise NextERPContractError("Resposta do NextERP não é um objeto JSON.")
        body = payload.get("message", payload)
        if not isinstance(body, dict):
            raise NextERPContractError("Corpo da resposta do NextERP é inválido.")
        version = body.get("contract_version") or body.get("version")
        if version != "v1":
            raise NextERPContractError(f"Contrato incompatível: esperado v1, recebido {version!r}.")
        records = body.get("data", body.get("records"))
        has_more = body.get("has_more")
        next_cursor = body.get("next_cursor")
        checkpoint_value = body.get("checkpoint")
        if not isinstance(records, list) or not isinstance(has_more, bool):
            raise NextERPContractError("Página incompleta: data/records ou has_more inválido.")
        if has_more and not isinstance(next_cursor, str):
            raise NextERPContractError("Página incompleta: next_cursor obrigatório.")
        if not isinstance(checkpoint_value, str):
            raise NextERPContractError("Página incompleta: checkpoint obrigatório.")
        try:
            checkpoint = datetime.fromisoformat(checkpoint_value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise NextERPContractError("Página com checkpoint inválido.") from exc
        for record in records:
            if not isinstance(record, dict) or not record.get("name"):
                raise NextERPContractError("Registro sem objeto JSON ou identificador name.")
            modified = record.get("modified")
            if not isinstance(modified, str):
                raise NextERPContractError("Registro sem data modified da origem.")
            try:
                datetime.fromisoformat(modified.replace("Z", "+00:00"))
            except ValueError as exc:
                raise NextERPContractError("Registro com data modified inválida.") from exc
        return DatasetPage(records, next_cursor or "", has_more, version, checkpoint)

    @staticmethod
    def _validate_catalog(payload):
        if not isinstance(payload, dict):
            raise NextERPContractError("Catálogo do NextERP não é um objeto JSON.")
        body = payload.get("message", payload)
        if not isinstance(body, dict) or body.get("contract_version") != "v1":
            raise NextERPContractError("Catálogo do NextERP não usa o contrato v1.")
        datasets = body.get("datasets")
        if not isinstance(datasets, list):
            raise NextERPContractError("Catálogo do NextERP não informa os conjuntos.")
        warehouses = next(
            (item for item in datasets if isinstance(item, dict) and item.get("id") == "warehouses"),
            None,
        )
        if not warehouses or warehouses.get("read_only") is not True:
            raise NextERPContractError("Catálogo sem conjunto warehouses somente leitura.")
        return body

    @staticmethod
    def _validate_ongsys_warehouse_mappings(payload):
        if not isinstance(payload, dict):
            raise NextERPContractError("Mapeamentos do NextERP não são um objeto JSON.")
        mappings = payload.get("message")
        if not isinstance(mappings, list):
            raise NextERPContractError("Resposta sem lista de mapeamentos ONGSYS.")
        validated = []
        for mapping in mappings:
            if not isinstance(mapping, dict):
                raise NextERPContractError("Mapeamento ONGSYS inválido.")
            code = mapping.get("cost_center_code")
            warehouse = mapping.get("warehouse")
            status = mapping.get("status")
            if not isinstance(code, str) or not code.strip():
                raise NextERPContractError("Mapeamento ONGSYS sem centro de custo.")
            if warehouse is not None and not isinstance(warehouse, str):
                raise NextERPContractError("Mapeamento ONGSYS com armazém inválido.")
            if not isinstance(status, str) or not status.strip():
                raise NextERPContractError("Mapeamento ONGSYS sem situação.")
            validated.append(mapping)
        return validated
