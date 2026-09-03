import logging

import requests
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.integrations.models import OngsysEndpointStatus, OngsysTask


logger = logging.getLogger(__name__)

SAFE_HEALTH_CHECKS = [
    ("fornecedores-get", "fornecedores", {"pageNumber": 1}),
    ("clientes-get", "clientes", {"pageNumber": 1}),
    ("produtos-get", "produtos", {"pageNumber": 1}),
    ("contratos-pagar-get", "contratos", {"pageNumber": 1}),
    ("contratos-receber-get", "contratos-receber", {"pageNumber": 1}),
    ("lancamentos-bancarios-get", "lancamentos-bancarios", {"data_inicio": "2026-01-01", "data_fim": "2026-12-31", "pageNumber": 1}),
    ("transferencias-bancarias-get", "transferencias-bancarias", {"data_inicio": "2026-01-01", "data_fim": "2026-12-31", "pageNumber": 1}),
    ("adiantamentos-fornecedores-get", "adiantamentos-fornecedores", {"data_inicio": "2026-01-01", "data_fim": "2026-12-31", "pageNumber": 1}),
    ("adiantamentos-clientes-get", "adiantamentos-clientes", {"data_inicio": "2026-01-01", "data_fim": "2026-12-31", "pageNumber": 1}),
    ("contas-pagar-get", "contas-pagar", {"filtro": 1, "data_inicio": "2025-07-01", "data_fim": "2026-12-31", "pageNumber": 1}),
    ("contas-receber-get", "contas-receber", {"filtro": 1, "data_inicio": "2025-07-01", "data_fim": "2026-12-31", "pageNumber": 1}),
    ("nfse-get", "notas-servico", {"pageNumber": 1}),
    ("nfe-get", "notas-produto", {"pageNumber": 1}),
    ("logs-get", "logs", {"data_inicio": "2026-01-01", "data_fim": "2026-12-31", "pageNumber": 1}),
]


def claim_task(task_id=None):
    """Claim exactly one queued task; concurrent workers cannot claim it twice."""
    try:
        with transaction.atomic():
            queryset = OngsysTask.objects.select_for_update(skip_locked=True).filter(
                status=OngsysTask.Status.QUEUED
            )
            if task_id:
                queryset = queryset.filter(pk=task_id)
            task = queryset.order_by("criado_em").first()
            if not task:
                return None
            task.status = OngsysTask.Status.RUNNING
            task.iniciado_em = timezone.now()
            task.progresso_pct = max(task.progresso_pct, 1)
            task.etapa_atual = "Tarefa assumida pelo executor."
            task.save(
                update_fields=[
                    "status", "iniciado_em", "progresso_pct", "etapa_atual", "atualizado_em"
                ]
            )
            return task
    except IntegrityError:
        logger.info("Tarefa OngSys concorrente já está em execução.")
        return None


def _sync_steps(entity, pages):
    from apps.integrations.ongsys_sync import (
        sync_clientes,
        sync_contas_pagar,
        sync_contas_receber,
        sync_contratos,
        sync_fornecedores,
        sync_lancamentos_bancarios,
        sync_logs,
        sync_notas_produto,
        sync_notas_servico,
        sync_produtos,
    )

    all_steps = {
        "fornecedores": ("Fornecedores", lambda: sync_fornecedores(max_pages=pages)),
        "clientes": ("Clientes", lambda: sync_clientes(max_pages=pages)),
        "contas_pagar": ("Contas a Pagar", lambda: sync_contas_pagar(max_pages=pages)),
        "contas_receber": ("Contas a Receber", lambda: sync_contas_receber(max_pages=pages)),
        "lancamentos_bancarios": ("Lançamentos Bancários", lambda: sync_lancamentos_bancarios(max_pages=pages)),
        "contratos": ("Contratos", lambda: sync_contratos(max_pages=pages)),
        "produtos": ("Produtos", lambda: sync_produtos(max_pages=pages)),
        "notas_servico": ("Notas de Serviço", lambda: sync_notas_servico(max_pages=pages)),
        "notas_produto": ("Notas de Produto", lambda: sync_notas_produto(max_pages=pages)),
        "logs": ("Logs de Auditoria", lambda: sync_logs(max_pages=pages)),
    }
    aliases = {
        "lancamentos": "lancamentos_bancarios",
        "nfse": "notas_servico",
        "nfe": "notas_produto",
    }
    entity = aliases.get(entity, entity)
    if entity == "all":
        return list(all_steps.values())
    if entity not in all_steps:
        raise ValueError("Entidade de sincronização não permitida.")
    return [all_steps[entity]]


def _save_progress(task, completed, total, step, results):
    task.itens_concluidos = completed
    task.total_itens = total
    task.progresso_pct = min(99, int(completed / max(total, 1) * 100))
    task.etapa_atual = step
    task.resultados = results
    task.save(
        update_fields=[
            "itens_concluidos", "total_itens", "progresso_pct", "etapa_atual",
            "resultados", "atualizado_em",
        ]
    )


def _process_sync(task):
    steps = _sync_steps(task.entidade, task.paginas)
    results = []
    for index, (name, function) in enumerate(steps, 1):
        task.etapa_atual = f"Sincronizando {name} ({index}/{len(steps)})."
        task.save(update_fields=["etapa_atual", "atualizado_em"])
        try:
            result = function()
            result["status"] = "completed"
        except Exception as exc:
            logger.exception("Falha na tarefa OngSys %s (%s)", task.pk, name)
            result = {"entidade": name, "status": "error", "erro": str(exc)[:1000]}
        results.append(result)
        _save_progress(task, index, len(steps), task.etapa_atual, results)
    return results


def _process_health_checks(task):
    from apps.integrations.ongsys_credentials import get_ongsys_credentials, get_ongsys_headers

    credentials = get_ongsys_credentials()
    headers = get_ongsys_headers()
    base_url = credentials.base_url.rstrip("/")
    results = []
    for index, (endpoint_id, path, params) in enumerate(SAFE_HEALTH_CHECKS, 1):
        params = dict(params)
        today = timezone.localdate()
        if 'data_inicio' in params:
            params['data_inicio'] = today.replace(month=1, day=1).isoformat()
        if 'data_fim' in params:
            params['data_fim'] = today.isoformat()
        task.etapa_atual = f"Testando /{path} ({index}/{len(SAFE_HEALTH_CHECKS)})."
        task.save(update_fields=["etapa_atual", "atualizado_em"])
        started = timezone.now()
        try:
            response = requests.get(
                f"{base_url}/{path}", headers=headers, params=params, timeout=10
            )
            elapsed_ms = max(0, int((timezone.now() - started).total_seconds() * 1000))
            classification = "success" if response.status_code == 200 else "error"
            result = {
                "ep_id": endpoint_id,
                "path": path,
                "method": "GET",
                "status_code": response.status_code,
                "latency_ms": elapsed_ms,
                "classification": classification,
            }
            now = timezone.now()
            defaults = {
                "endpoint_path": path,
                "metodo": "GET",
                "ultimo_status_http": response.status_code,
                "status_classificacao": classification,
                "latencia_ms": elapsed_ms,
                "ultima_vez_testado": now,
            }
            if classification == "success":
                defaults["ultima_vez_sucesso"] = now
            OngsysEndpointStatus.objects.update_or_create(
                endpoint_id=endpoint_id, defaults=defaults
            )
        except requests.RequestException as exc:
            now = timezone.now()
            result = {
                "ep_id": endpoint_id,
                "path": path,
                "method": "GET",
                "status_code": 0,
                "latency_ms": 0,
                "classification": "error",
                "error": exc.__class__.__name__,
            }
            OngsysEndpointStatus.objects.update_or_create(
                endpoint_id=endpoint_id,
                defaults={
                    "endpoint_path": path,
                    "metodo": "GET",
                    "ultimo_status_http": 0,
                    "status_classificacao": "error",
                    "latencia_ms": 0,
                    "ultima_vez_testado": now,
                },
            )
        results.append(result)
        _save_progress(task, index, len(SAFE_HEALTH_CHECKS), task.etapa_atual, results)
    return results


def process_claimed_task(task):
    try:
        if task.tipo == OngsysTask.Tipo.SYNC_DB:
            results = _process_sync(task)
        elif task.tipo == OngsysTask.Tipo.TEST_ALL:
            results = _process_health_checks(task)
        else:
            raise ValueError("Tipo de tarefa OngSys não permitido.")

        failures = [result for result in results if result.get("status") == "error" or result.get("classification") == "error"]
        task.status = (
            OngsysTask.Status.COMPLETED
            if not failures
            else OngsysTask.Status.ERROR
            if len(failures) == len(results)
            else OngsysTask.Status.PARTIAL
        )
        task.erro = "; ".join(result.get("erro") or result.get("error", "") for result in failures)[:4000]
        task.resultados = results
    except Exception as exc:
        logger.exception("Falha irrecuperável na tarefa OngSys %s", task.pk)
        task.status = OngsysTask.Status.ERROR
        task.erro = str(exc)[:4000]
    task.progresso_pct = 100
    task.finalizado_em = timezone.now()
    task.etapa_atual = (
        "Tarefa concluída com sucesso."
        if task.status == OngsysTask.Status.COMPLETED
        else "Tarefa encerrada com falhas."
    )
    task.save()
    return task
