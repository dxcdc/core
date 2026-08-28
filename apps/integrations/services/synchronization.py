import uuid

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.integrations.models import (
    IntegrationCheckpoint,
    IntegrationStagingRecord,
    IntegrationSyncRun,
    IntegrationSystem,
    Warehouse,
)
from apps.integrations.services.nexterp import NextERPError


def _source_modified(record):
    value = record.get("modified")
    return parse_datetime(value) if isinstance(value, str) else value


class WarehouseSynchronizer:
    dataset = "warehouses"

    def __init__(self, client):
        self.client = client

    def run(self):
        system, _ = IntegrationSystem.objects.get_or_create(
            slug="nexterp",
            defaults={
                "name": "NextERP",
                "base_url": self.client.base_url,
                "direction": IntegrationSystem.Direction.SOURCE,
            },
        )
        started_at = timezone.now()
        with transaction.atomic():
            checkpoint, _ = IntegrationCheckpoint.objects.select_for_update().get_or_create(
                system=system, dataset=self.dataset
            )
            modified_since = checkpoint.resume_modified_since or checkpoint.completed_through
            cursor = checkpoint.resume_cursor
            run = IntegrationSyncRun.objects.create(
                system=system,
                dataset=self.dataset,
                correlation_id=uuid.uuid4(),
                modified_since=modified_since,
                started_at=started_at,
            )
            if not checkpoint.resume_modified_since:
                checkpoint.resume_modified_since = modified_since
            checkpoint.last_run = run
            checkpoint.save()

        try:
            provider_checkpoint = None
            while True:
                page = self.client.fetch_dataset_page(
                    self.dataset,
                    cursor=cursor,
                    modified_since=modified_since,
                    correlation_id=run.correlation_id,
                )
                if provider_checkpoint and page.checkpoint != provider_checkpoint:
                    raise NextERPError("O checkpoint do NextERP mudou durante a paginação.")
                provider_checkpoint = page.checkpoint
                with transaction.atomic():
                    inserted = updated = 0
                    for record in page.records:
                        _, staging_created = IntegrationStagingRecord.objects.update_or_create(
                            system=system,
                            dataset=self.dataset,
                            source_name=record["name"],
                            defaults={
                                "source_modified": _source_modified(record),
                                "raw_payload": record,
                                "contract_version": page.contract_version,
                                "imported_by_run": run,
                                "active": True,
                            },
                        )
                        _, warehouse_created = Warehouse.objects.update_or_create(
                            system=system,
                            source_name=record["name"],
                            defaults={
                                "warehouse_name": record.get("warehouse_name") or record.get("name"),
                                "project_id": record.get("project_id") or "",
                                "source_modified": _source_modified(record),
                                "active": not bool(record.get("disabled", False)),
                                "imported_by_run": run,
                            },
                        )
                        if staging_created or warehouse_created:
                            inserted += 1
                        else:
                            updated += 1

                    run.pages_processed += 1
                    run.records_received += len(page.records)
                    run.records_inserted += inserted
                    run.records_updated += updated
                    run.attempts += self.client.last_attempts
                    run.last_cursor = page.next_cursor
                    run.save()

                    checkpoint = IntegrationCheckpoint.objects.select_for_update().get(pk=checkpoint.pk)
                    checkpoint.resume_cursor = page.next_cursor
                    checkpoint.last_run = run
                    checkpoint.save()

                if not page.has_more:
                    break
                cursor = page.next_cursor

            with transaction.atomic():
                run.status = IntegrationSyncRun.Status.SUCCEEDED
                run.finished_at = timezone.now()
                run.save()
                checkpoint = IntegrationCheckpoint.objects.select_for_update().get(pk=checkpoint.pk)
                checkpoint.completed_through = provider_checkpoint
                checkpoint.resume_cursor = ""
                checkpoint.resume_modified_since = None
                checkpoint.last_run = run
                checkpoint.save()
            return run
        except Exception as exc:
            run.status = IntegrationSyncRun.Status.FAILED
            run.finished_at = timezone.now()
            run.attempts += self.client.last_attempts
            run.error_code = getattr(exc, "code", "unexpected_error")
            error_message = str(exc)
            for sensitive_value in (
                getattr(self.client, "api_key", ""),
                getattr(self.client, "api_secret", ""),
            ):
                if sensitive_value:
                    error_message = error_message.replace(sensitive_value, "[REDACTED]")
            run.error_message = error_message[:2000]
            run.save()
            raise
