import json

from django.core.management.base import BaseCommand, CommandError

from apps.integrations.ongsys_fiscal_discovery import (
    FISCAL_ENDPOINTS,
    OngsysFiscalDiscoveryError,
    discover_fiscal_endpoint,
)


class Command(BaseCommand):
    help = "Descobre somente a estrutura das APIs fiscais OngSys, sem gravar notas."

    def add_arguments(self, parser):
        parser.add_argument("kind", choices=sorted(FISCAL_ENDPOINTS))
        parser.add_argument("--since", required=True, help="Data inicial YYYY-MM-DD")
        parser.add_argument("--until", required=True, help="Data final YYYY-MM-DD")
        parser.add_argument("--pages", type=int, default=1)

    def handle(self, *args, **options):
        try:
            result = discover_fiscal_endpoint(
                options["kind"],
                options["since"],
                options["until"],
                max_pages=options["pages"],
            )
        except OngsysFiscalDiscoveryError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
        self.stdout.write(
            self.style.SUCCESS(
                "Descoberta concluída sem persistir ou exibir valores fiscais."
            )
        )
