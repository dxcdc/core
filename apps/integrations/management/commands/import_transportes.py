import os
import glob
import time
from django.core.management.base import BaseCommand
from apps.integrations.transportes_sync import processar_arquivo_transporte
from apps.integrations.models import TransporteCorrida


class Command(BaseCommand):
    help = "Importa arquivos CSV/XLSX de transporte (Uber e 99) para o PostgreSQL de forma atômica."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Caminho do arquivo ou diretório contendo arquivos da Uber e 99.",
        )
        parser.add_argument(
            "--plataforma",
            type=str,
            default="all",
            choices=["all", "uber", "99"],
            help="Filtrar por plataforma ao escanear diretórios (padrão: all).",
        )

    def handle(self, *args, **options):
        caminho = options["path"]
        filtro_plataforma = options["plataforma"]

        self.stdout.write(self.style.MIGRATE_HEADING("=== INICIANDO IMPORTAÇÃO ATÔMICA DE TRANSPORTES (UBER & 99) ==="))
        t_start = time.time()

        if os.path.isfile(caminho):
            arquivos = [caminho]
        elif os.path.isdir(caminho):
            arquivos = []
            # Procura por subpastas uber e 99 ou no próprio diretório
            for root, _, files in os.walk(caminho):
                if "venv" in root or ".git" in root:
                    continue
                for f in sorted(files):
                    if (
                        (f.endswith(".csv") or f.endswith(".xlsx"))
                        and not f.startswith(".")
                        and not f.startswith("~")
                        and "lock" not in f.lower()
                        and "relatorio_transportes" not in f.lower()
                    ):
                        full_path = os.path.join(root, f)
                        if filtro_plataforma == "uber" and "99" in root:
                            continue
                        if filtro_plataforma == "99" and "uber" in root:
                            continue
                        arquivos.append(full_path)
        else:
            self.stderr.write(self.style.ERROR(f"Caminho inválido: {caminho}"))
            return

        self.stdout.write(f"Encontrados {len(arquivos)} arquivo(s) para processar.\n")

        total_corridas = 0
        total_valor = 0.0

        for idx, arq in enumerate(arquivos, 1):
            nome_arq = os.path.basename(arq)
            try:
                res = processar_arquivo_transporte(arq, nome_arquivo=nome_arq)
                total_corridas += res["total_salvo"]
                total_valor += res["valor_total_brl"]
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{idx}/{len(arquivos)}] ✔ {nome_arq} ({res['plataforma']}): {res['total_salvo']} corridas salvas | R$ {res['valor_total_brl']:,.2f}"
                    )
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"[{idx}/{len(arquivos)}] ❌ Erro em {nome_arq}: {e}"))

        duracao = round(time.time() - t_start, 2)
        total_db = TransporteCorrida.objects.count()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== RESUMO DA IMPORTAÇÃO ==="))
        self.stdout.write(self.style.SUCCESS(f"✔ Corridas processadas nesta execução: {total_corridas}"))
        self.stdout.write(self.style.SUCCESS(f"✔ Valor total movimentado: R$ {total_valor:,.2f}"))
        self.stdout.write(self.style.SUCCESS(f"✔ Total acumulado no PostgreSQL: {total_db} corridas"))
        self.stdout.write(self.style.SUCCESS(f"🚀 Tempo total: {duracao} segundos!"))
