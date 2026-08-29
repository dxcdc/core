import os
import re
import time
import base64
import logging
import requests
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from apps.integrations.models import (
    OngsysFornecedor,
    OngsysCliente,
    OngsysContaPagar,
    OngsysContaReceber,
    OngsysLancamentoBancario,
    OngsysContrato,
    OngsysProduto,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.ongsys.com.br/app/index.php/api/v2/"


def get_headers():
    cnpj = os.environ.get("ONGSYS_CNPJ", "03970166000129")
    cnpj = re.sub(r"\D", "", cnpj)
    api_key = os.environ.get("ONGSYS_API_KEY", "")
    auth_b64 = base64.b64encode(f"{cnpj}:{api_key}".encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(str(date_str).strip()[:10], fmt[:10]).date()
        except (ValueError, TypeError):
            continue
    return None


def parse_decimal(val):
    if val is None or val == "":
        return Decimal("0.00")
    try:
        val_str = str(val).replace(".", "").replace(",", ".") if "," in str(val) else str(val)
        return Decimal(val_str)
    except Exception:
        return Decimal("0.00")


# ==============================================================================
# 1. FORNECEDORES (ATÔMICO)
# ==============================================================================
def sync_fornecedores(max_pages=None):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    while True:
        if max_pages and page > max_pages:
            break

        try:
            resp = requests.get(
                f"{BASE_URL}fornecedores",
                headers=headers,
                params={"pageNumber": page},
                timeout=20,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                id_val = str(item.get("id") or item.get("idFornecedor") or "").strip()
                if not id_val:
                    continue
                objs.append(
                    OngsysFornecedor(
                        id_ongsys=id_val,
                        documento=str(item.get("documento") or "").strip(),
                        nome_empresa=str(item.get("nomeEmpresa") or item.get("nome") or "Sem Nome").strip()[:255],
                        nome_fantasia=str(item.get("nomeFantasia") or "").strip()[:255] or None,
                        tipo_pessoa=str(item.get("pessoa") or "").strip()[:32],
                        tipo_fornecedor=str(item.get("tipoFornecedor") or "").strip()[:64],
                        ativo_inativo=str(item.get("ativoInativo") or "A").strip()[:8],
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysFornecedor.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["id_ongsys"],
                    update_fields=[
                        "documento",
                        "nome_empresa",
                        "nome_fantasia",
                        "tipo_pessoa",
                        "tipo_fornecedor",
                        "ativo_inativo",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar fornecedores pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Fornecedores", "total": total_processed, "duracao": duracao}


# ==============================================================================
# 2. CLIENTES / PROJETOS (ATÔMICO)
# ==============================================================================
def sync_clientes(max_pages=None):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    while True:
        if max_pages and page > max_pages:
            break

        try:
            resp = requests.get(
                f"{BASE_URL}clientes",
                headers=headers,
                params={"pageNumber": page},
                timeout=20,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                id_val = str(item.get("id") or item.get("idCliente") or "").strip()
                if not id_val:
                    continue
                objs.append(
                    OngsysCliente(
                        id_ongsys=id_val,
                        documento=str(item.get("documento") or "").strip(),
                        nome_empresa=str(item.get("nomeEmpresa") or item.get("nome") or "Sem Nome").strip()[:255],
                        nome_fantasia=str(item.get("nomeFantasia") or "").strip()[:255] or None,
                        tipo_pessoa=str(item.get("pessoa") or "").strip()[:32],
                        tipo_cliente=str(item.get("tipoCliente") or "").strip()[:64],
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysCliente.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["id_ongsys"],
                    update_fields=[
                        "documento",
                        "nome_empresa",
                        "nome_fantasia",
                        "tipo_pessoa",
                        "tipo_cliente",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar clientes pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Clientes", "total": total_processed, "duracao": duracao}


# ==============================================================================
# 3. CONTAS A PAGAR (ATÔMICO)
# ==============================================================================
def sync_contas_pagar(max_pages=None, data_inicio="2025-07-01", data_fim="2026-12-31"):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    while True:
        if max_pages and page > max_pages:
            break

        try:
            resp = requests.get(
                f"{BASE_URL}contas-pagar",
                headers=headers,
                params={
                    "filtro": 1,
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "pageNumber": page,
                },
                timeout=25,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                cod = str(item.get("codLancamento") or item.get("id") or "").strip()
                if not cod:
                    continue
                forn = item.get("fornecedor") or {}
                
                # Extração de Rateios Contábeis e Projetos
                rateios = item.get("rateios") or []
                r0 = rateios[0] if isinstance(rateios, list) and len(rateios) > 0 else {}
                proj_nome = str(r0.get("projeto") or item.get("projeto") or "")[:255]
                subproj_nome = str(r0.get("subprojeto") or item.get("subprojeto") or "")[:255]
                conta_cont = str(r0.get("conta") or item.get("contaContabil") or "")[:255]

                # Extração de Baixas / Pagamentos
                baixas = item.get("baixaTipo") or []
                b0 = baixas[0] if isinstance(baixas, list) and len(baixas) > 0 else {}
                dt_pag = parse_date(b0.get("data") or item.get("dataPagamento"))
                vl_pag = parse_decimal(b0.get("valor") or item.get("valorPago"))
                vl_tot = parse_decimal(item.get("valorBruto") or item.get("valorLiquido") or item.get("valorTotal") or item.get("valor"))

                objs.append(
                    OngsysContaPagar(
                        cod_lancamento=cod,
                        fornecedor_nome=str(forn.get("nome") or forn.get("nomeEmpresa") or "").strip()[:255],
                        fornecedor_documento=str(forn.get("documento") or "").strip()[:32],
                        historico_despesa=str(item.get("historicoDespesa") or item.get("historico") or ""),
                        tipo_despesa=str(item.get("tipoDespesa") or "")[:120],
                        data_emissao=parse_date(item.get("dataEmissao")),
                        data_vencimento=parse_date(item.get("dataVencimento")),
                        data_pagamento=dt_pag,
                        valor_total=vl_tot,
                        valor_pago=vl_pag,
                        status_pagamento=str(item.get("statusAprovacao") or item.get("status") or "")[:64],
                        projeto_nome=proj_nome,
                        subprojeto_nome=subproj_nome,
                        conta_contabil=conta_cont,
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysContaPagar.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["cod_lancamento"],
                    update_fields=[
                        "fornecedor_nome",
                        "fornecedor_documento",
                        "historico_despesa",
                        "tipo_despesa",
                        "data_emissao",
                        "data_vencimento",
                        "data_pagamento",
                        "valor_total",
                        "valor_pago",
                        "status_pagamento",
                        "projeto_nome",
                        "subprojeto_nome",
                        "conta_contabil",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar contas a pagar pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Contas a Pagar", "total": total_processed, "duracao": duracao}


# ==============================================================================
# 4. CONTAS A RECEBER (ATÔMICO)
# ==============================================================================
def sync_contas_receber(max_pages=None, data_inicio="2025-07-01", data_fim="2026-12-31"):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    while True:
        if max_pages and page > max_pages:
            break

        try:
            resp = requests.get(
                f"{BASE_URL}contas-receber",
                headers=headers,
                params={
                    "filtro": 1,
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "pageNumber": page,
                },
                timeout=25,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                cod = str(item.get("codLancamento") or item.get("id") or "").strip()
                if not cod:
                    continue
                cli = item.get("cliente") or {}

                # Extração de Rateios e Projetos
                rateios = item.get("rateios") or []
                r0 = rateios[0] if isinstance(rateios, list) and len(rateios) > 0 else {}
                proj_nome = str(r0.get("projeto") or item.get("projeto") or "")[:255]
                conta_cont = str(r0.get("conta") or item.get("contaContabil") or "")[:255]

                # Extração de Baixas / Recebimentos
                baixas = item.get("baixaTipo") or []
                b0 = baixas[0] if isinstance(baixas, list) and len(baixas) > 0 else {}
                dt_rec = parse_date(b0.get("data") or item.get("dataRecebimento"))
                vl_rec = parse_decimal(b0.get("valor") or item.get("valorRecebido"))
                vl_tot = parse_decimal(item.get("valorBruto") or item.get("valorLiquido") or item.get("valorTotal") or item.get("valor"))

                objs.append(
                    OngsysContaReceber(
                        cod_lancamento=cod,
                        cliente_nome=str(cli.get("nome") or cli.get("nomeEmpresa") or "").strip()[:255],
                        cliente_documento=str(cli.get("documento") or "").strip()[:32],
                        historico_receita=str(item.get("historicoReceita") or item.get("historico") or ""),
                        tipo_receita=str(item.get("tipoReceita") or "")[:120],
                        data_emissao=parse_date(item.get("dataEmissao")),
                        data_vencimento=parse_date(item.get("dataVencimento")),
                        data_recebimento=dt_rec,
                        valor_total=vl_tot,
                        valor_recebido=vl_rec,
                        status_recebimento=str(item.get("status") or item.get("statusAprovacao") or "")[:64],
                        projeto_nome=proj_nome,
                        conta_contabil=conta_cont,
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysContaReceber.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["cod_lancamento"],
                    update_fields=[
                        "cliente_nome",
                        "cliente_documento",
                        "historico_receita",
                        "tipo_receita",
                        "data_emissao",
                        "data_vencimento",
                        "data_recebimento",
                        "valor_total",
                        "valor_recebido",
                        "status_recebimento",
                        "projeto_nome",
                        "conta_contabil",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar contas a receber pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Contas a Receber", "total": total_processed, "duracao": duracao}


# ==============================================================================
# 5. LANÇAMENTOS BANCÁRIOS (ATÔMICO)
# ==============================================================================
def sync_lancamentos_bancarios(max_pages=None, data_inicio="2024-01-01", data_fim="2026-12-31"):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    while True:
        if max_pages and page > max_pages:
            break

        try:
            resp = requests.get(
                f"{BASE_URL}lancamentos-bancarios",
                headers=headers,
                params={
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "pageNumber": page,
                },
                timeout=25,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                cod = str(item.get("codigo") or item.get("id") or "").strip()
                if not cod:
                    continue
                objs.append(
                    OngsysLancamentoBancario(
                        codigo=cod,
                        data_operacao=parse_date(item.get("dataOperacao")),
                        conta_bancaria=str(item.get("contaBancaria") or "")[:255],
                        tipo_operacao=str(item.get("tipo") or "")[:16],
                        valor=parse_decimal(item.get("valor")),
                        categoria=str(item.get("categoria") or "")[:120],
                        descricao=str(item.get("descricao") or ""),
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysLancamentoBancario.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["codigo"],
                    update_fields=[
                        "data_operacao",
                        "conta_bancaria",
                        "tipo_operacao",
                        "valor",
                        "categoria",
                        "descricao",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar lançamentos bancários pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Lançamentos Bancários", "total": total_processed, "duracao": duracao}


# ==============================================================================
# 6. CONTRATOS (ATÔMICO)
# ==============================================================================
def sync_contratos(max_pages=None):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    # Contratos a Pagar
    while True:
        if max_pages and page > max_pages:
            break
        try:
            resp = requests.get(
                f"{BASE_URL}contratos",
                headers=headers,
                params={"pageNumber": page},
                timeout=20,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                id_val = f"PAGAR_{item.get('id')}"
                forn = item.get("fornecedor") or {}
                objs.append(
                    OngsysContrato(
                        id_ongsys=id_val,
                        codigo=str(item.get("codigo") or "")[:64],
                        tipo_contrato="PAGAR",
                        nome_contraparte=str(forn.get("nome") or "")[:255],
                        documento_contraparte=str(forn.get("dcto") or forn.get("documento") or "")[:32],
                        nome_contrato=str(item.get("nomeContrato") or "Sem Título")[:255],
                        descricao_contrato=str(item.get("descricaoContrato") or ""),
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysContrato.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["id_ongsys"],
                    update_fields=[
                        "codigo",
                        "tipo_contrato",
                        "nome_contraparte",
                        "documento_contraparte",
                        "nome_contrato",
                        "descricao_contrato",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar contratos pagar pág {page}: {e}")
            break

    # Contratos a Receber
    page = 1
    while True:
        if max_pages and page > max_pages:
            break
        try:
            resp = requests.get(
                f"{BASE_URL}contratos-receber",
                headers=headers,
                params={"pageNumber": page},
                timeout=20,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                id_val = f"RECEBER_{item.get('id')}"
                cli = item.get("cliente") or {}
                objs.append(
                    OngsysContrato(
                        id_ongsys=id_val,
                        codigo=str(item.get("codigo") or "")[:64],
                        tipo_contrato="RECEBER",
                        nome_contraparte=str(cli.get("nome") or "")[:255],
                        documento_contraparte=str(cli.get("dcto") or cli.get("documento") or "")[:32],
                        nome_contrato=str(item.get("nomeContrato") or "Sem Título")[:255],
                        descricao_contrato=str(item.get("descricaoContrato") or ""),
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysContrato.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["id_ongsys"],
                    update_fields=[
                        "codigo",
                        "tipo_contrato",
                        "nome_contraparte",
                        "documento_contraparte",
                        "nome_contrato",
                        "descricao_contrato",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar contratos receber pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Contratos", "total": total_processed, "duracao": duracao}


# ==============================================================================
# 7. PRODUTOS (ATÔMICO)
# ==============================================================================
def sync_produtos(max_pages=None):
    headers = get_headers()
    page = 1
    total_processed = 0
    t0 = time.time()

    while True:
        if max_pages and page > max_pages:
            break

        try:
            resp = requests.get(
                f"{BASE_URL}produtos",
                headers=headers,
                params={"pageNumber": page},
                timeout=20,
            )
            if resp.status_code != 200:
                break
            payload = resp.json()
            items = payload.get("data", [])
            if not items:
                break

            objs = []
            for item in items:
                id_val = str(item.get("id") or item.get("idProduto") or "").strip()
                if not id_val:
                    continue
                objs.append(
                    OngsysProduto(
                        id_ongsys=id_val,
                        nome_produto=str(item.get("nomeProduto") or "Sem Nome")[:255],
                        descricao_produto=str(item.get("descricaoProduto") or ""),
                        status=str(item.get("status") or "ativo")[:32],
                        grupo=str(item.get("grupo") or "")[:120] or None,
                        unidade_medida=str(item.get("unidadeMedida") or "")[:64] or None,
                        valor_custo=parse_decimal(item.get("valorCustoBase") or item.get("valorCusto")),
                        dados_brutos=item,
                    )
                )

            with transaction.atomic():
                OngsysProduto.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["id_ongsys"],
                    update_fields=[
                        "nome_produto",
                        "descricao_produto",
                        "status",
                        "grupo",
                        "unidade_medida",
                        "valor_custo",
                        "dados_brutos",
                        "atualizado_em",
                    ],
                )

            total_processed += len(objs)
            page += 1
            if len(items) < 100:
                break
        except Exception as e:
            logger.error(f"Erro ao sincronizar produtos pág {page}: {e}")
            break

    duracao = round(time.time() - t0, 2)
    return {"entidade": "Produtos", "total": total_processed, "duracao": duracao}


# ==============================================================================
# SINCRONIZAÇÃO COMPLETA
# ==============================================================================
def sync_all_ongsys(max_pages_per_entity=3):
    results = []
    results.append(sync_fornecedores(max_pages=max_pages_per_entity))
    results.append(sync_clientes(max_pages=max_pages_per_entity))
    results.append(sync_contratos(max_pages=max_pages_per_entity))
    results.append(sync_produtos(max_pages=max_pages_per_entity))
    results.append(sync_contas_pagar(max_pages=max_pages_per_entity))
    results.append(sync_contas_receber(max_pages=max_pages_per_entity))
    results.append(sync_lancamentos_bancarios(max_pages=max_pages_per_entity))
    return results
