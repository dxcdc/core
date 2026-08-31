import hashlib
import json
from dataclasses import dataclass
from datetime import date

import requests

from apps.integrations.ongsys_credentials import (
    get_ongsys_credentials,
    get_ongsys_headers,
)


FISCAL_ENDPOINTS = {
    "nfse": "notas-servico",
    "nfe": "notas-produto",
}


class OngsysFiscalDiscoveryError(RuntimeError):
    pass


def _iso_date(value):
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (TypeError, ValueError) as exc:
        raise OngsysFiscalDiscoveryError(
            f"Data inválida: {value!r}. Use YYYY-MM-DD."
        ) from exc


def _shape(value, depth=0):
    if depth >= 4:
        return type(value).__name__
    if isinstance(value, dict):
        return {
            str(key): _shape(child, depth + 1)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_shape(value[0], depth + 1)] if value else []
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def _records(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise OngsysFiscalDiscoveryError("Resposta OngSys não é um objeto ou lista JSON.")
    data = payload.get("data", [])
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "registros", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    raise OngsysFiscalDiscoveryError("Não foi possível localizar a lista de registros.")


@dataclass(frozen=True)
class FiscalDiscoveryResult:
    endpoint: str
    pages_read: int
    records_seen: int
    page_hashes: tuple[str, ...]
    response_shape: object
    record_shape: object

    def as_dict(self):
        return {
            "endpoint": self.endpoint,
            "pages_read": self.pages_read,
            "records_seen": self.records_seen,
            "page_hashes": list(self.page_hashes),
            "response_shape": self.response_shape,
            "record_shape": self.record_shape,
        }


def discover_fiscal_endpoint(kind, since, until, max_pages=1, session=None):
    if kind not in FISCAL_ENDPOINTS:
        raise OngsysFiscalDiscoveryError(f"Tipo fiscal desconhecido: {kind!r}.")
    since = _iso_date(since)
    until = _iso_date(until)
    if since > until:
        raise OngsysFiscalDiscoveryError("Data inicial não pode ser posterior à final.")
    if not 1 <= int(max_pages) <= 20:
        raise OngsysFiscalDiscoveryError("A descoberta aceita entre 1 e 20 páginas.")

    credentials = get_ongsys_credentials()
    headers = get_ongsys_headers()
    client = session or requests.Session()
    endpoint = FISCAL_ENDPOINTS[kind]
    hashes = []
    records_seen = 0
    response_shape = None
    record_shape = None

    for page in range(1, int(max_pages) + 1):
        try:
            response = client.get(
                f"{credentials.base_url}{endpoint}",
                headers=headers,
                params={
                    "data_inicio": since,
                    "data_fim": until,
                    "pageNumber": page,
                },
                timeout=(10, 90),
            )
        except requests.RequestException as exc:
            raise OngsysFiscalDiscoveryError(
                f"Falha de conexão com OngSys em {endpoint}, página {page}."
            ) from exc
        if response.status_code != 200:
            raise OngsysFiscalDiscoveryError(
                f"OngSys recusou {endpoint}, página {page}: HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise OngsysFiscalDiscoveryError(
                f"OngSys retornou conteúdo não JSON em {endpoint}, página {page}."
            ) from exc

        canonical = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        if digest in hashes:
            break
        hashes.append(digest)
        page_records = _records(payload)
        if response_shape is None:
            response_shape = _shape(payload)
        if page_records and record_shape is None:
            record_shape = _shape(page_records[0])
        records_seen += len(page_records)
        if not page_records:
            break

    return FiscalDiscoveryResult(
        endpoint=endpoint,
        pages_read=len(hashes),
        records_seen=records_seen,
        page_hashes=tuple(hashes),
        response_shape=response_shape,
        record_shape=record_shape,
    )
