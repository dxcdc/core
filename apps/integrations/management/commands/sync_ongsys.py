import time
from django.core.management.base import BaseCommand
from apps.integrations.ongsys_sync import (
    sync_fornecedores,
    sync_clientes,
    sync_contas_pagar,
    sync_contas_receber,
    sync_lancamentos_bancarios,
    sync_contratos,
    sync_produtos,
    sync_all_ongsys,
)


class Command(BaseCommand):
    help = "Sincroniza dados da API OngSys de forma atômica no PostgreSQL do CDC Core"

    def add_arguments(self, parser):
        parser.add_argument(
            "--entity",
            type=str,
            default="all",
            choices=[
                "all",
                "fornecedores",
                "clientes",
                "contas_pagar",
                "contas_receber",
                "lancamentos_bancarios",
                "contratos",
                "produtos",
            ],
            help="Qual entidade sincronizar (padrão: all)",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=5,
            help="Limite de páginas por entidade (0 para todas as páginas)",
        )
        parser.add_argument(
            "--since",
            type=str,
            default="2025-07-01",
            help="Data inicial no formato YYYY-MM-DD (janela padrão: 13 meses)",
        )
        parser.add_argument(
            "--until",
            type=str,
            default="2026-12-31",
            help="Data final no formato YYYY-MM-DD",
        )

    def handle(self, *args, **options):
        entity = options["entity"]
        max_pages = options["pages"] if options["pages"] > 0 else None
        since = options["since"]
        until = options["until"]

        self.stdout.write(self.style.MIGRATE_HEADING(f"=== INICIANDO SINCRONIZAÇÃO ATÔMICA ONGSYS ({entity}) ==="))
        t_start = time.time()

        if entity == "all":
            results = sync_all_ongsys(max_pages_per_entity=max_pages or 3)
            for res in results:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ {res['entidade']}: {res['total']} registros sincronizados em {res['duracao']}s"
                    )
                )
        elif entity == "fornecedores":
            res = sync_fornecedores(max_pages=max_pages)
            self.stdout.write(self.style.SUCCESS(f"✔ Fornecedores: {res['total']} sincronizados em {res['duracao']}s"))
        elif entity == "clientes":
            res = sync_clientes(max_pages=max_pages)
            self.stdout.write(self.style.SUCCESS(f"✔ Clientes: {res['total']} sincronizados em {res['duracao']}s"))
        elif entity == "contas_pagar":
            res = sync_contas_pagar(max_pages=max_pages, data_inicio=since, data_fim=until)
            self.stdout.write(self.style.SUCCESS(f"✔ Contas a Pagar: {res['total']} sincronizados em {res['duracao']}s"))
        elif entity == "contas_receber":
            res = sync_contas_receber(max_pages=max_pages, data_inicio=since, data_fim=until)
            self.stdout.write(self.style.SUCCESS(f"✔ Contas a Receber: {res['total']} sincronizados em {res['duracao']}s"))
        elif entity == "lancamentos_bancarios":
            res = sync_lancamentos_bancarios(max_pages=max_pages, data_inicio=since, data_fim=until)
            self.stdout.write(self.style.SUCCESS(f"✔ Lançamentos Bancários: {res['total']} sincronizados em {res['duracao']}s"))

        elif entity == "contratos":
            res = sync_contratos(max_pages=max_pages)
            self.stdout.write(self.style.SUCCESS(f"✔ Contratos: {res['total']} sincronizados em {res['duracao']}s"))
        elif entity == "produtos":
            res = sync_produtos(max_pages=max_pages)
            self.stdout.write(self.style.SUCCESS(f"✔ Produtos: {res['total']} sincronizados em {res['duracao']}s"))

        total_time = round(time.time() - t_start, 2)
        self.stdout.write(self.style.SUCCESS(f"\n🚀 Sincronização atômica finalizada em {total_time} segundos!"))
