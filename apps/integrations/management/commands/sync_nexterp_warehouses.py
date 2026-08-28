from django.core.management.base import BaseCommand, CommandError

from apps.integrations.services.nexterp import NextERPAnalyticsClient, NextERPError
from apps.integrations.services.synchronization import WarehouseSynchronizer


class Command(BaseCommand):
    help = "Sincroniza armazéns autorizados do NextERP de forma incremental e retomável."

    def handle(self, *args, **options):
        try:
            run = WarehouseSynchronizer(NextERPAnalyticsClient()).run()
        except NextERPError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Execução {run.correlation_id} concluída: "
                f"{run.pages_processed} páginas, {run.records_received} registros."
            )
        )
