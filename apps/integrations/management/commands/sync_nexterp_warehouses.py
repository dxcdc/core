from django.core.management.base import BaseCommand, CommandError

from apps.integrations.services.nexterp import NextERPAnalyticsClient, NextERPError
from apps.integrations.services.synchronization import WarehouseSynchronizer


class Command(BaseCommand):
    help = "Sincroniza armazéns autorizados do NextERP de forma incremental e retomável."

    def handle(self, *args, **options):
        try:
            client = NextERPAnalyticsClient()
            catalog = client.fetch_catalog()
            warehouse_contract = next(
                item for item in catalog["datasets"] if item["id"] == "warehouses"
            )
            self.stdout.write(
                f"Catálogo v1 validado: {warehouse_contract.get('records', 0)} armazéns autorizados."
            )
            run = WarehouseSynchronizer(client).run()
        except NextERPError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Execução {run.correlation_id} concluída: "
                f"{run.pages_processed} páginas, {run.records_received} registros."
            )
        )
