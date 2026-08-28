from datetime import datetime, timezone as dt_timezone

from django.test import TestCase

from apps.integrations.models import (
    IntegrationCheckpoint,
    IntegrationStagingRecord,
    IntegrationSyncRun,
    Warehouse,
)
from apps.integrations.services.nexterp import DatasetPage, NextERPServerError
from apps.integrations.services.synchronization import WarehouseSynchronizer


class FakeClient:
    base_url = "https://erp.example.test"
    last_attempts = 1

    def __init__(self, pages):
        self.pages = iter(pages)
        self.calls = []

    def fetch_dataset_page(self, dataset, *, cursor, modified_since, correlation_id):
        self.calls.append((dataset, cursor, modified_since, correlation_id))
        result = next(self.pages)
        if isinstance(result, Exception):
            raise result
        return result


class WarehouseSynchronizationTests(TestCase):
    page_one = DatasetPage(
        records=[{
            "name": "WH-001", "warehouse_name": "Central", "project_id": "P-01",
            "modified": "2026-08-28T10:00:00Z",
        }],
        next_cursor="cursor-2",
        has_more=True,
        contract_version="v1",
        checkpoint=datetime(2026, 8, 28, 10, 5, tzinfo=dt_timezone.utc),
    )

    def test_failure_keeps_cursor_and_does_not_advance_checkpoint(self):
        client = FakeClient([self.page_one, NextERPServerError("indisponível")])
        with self.assertRaises(NextERPServerError):
            WarehouseSynchronizer(client).run()
        checkpoint = IntegrationCheckpoint.objects.get(dataset="warehouses")
        self.assertEqual(checkpoint.resume_cursor, "cursor-2")
        self.assertIsNone(checkpoint.completed_through)
        self.assertEqual(IntegrationSyncRun.objects.get().status, "failed")

    def test_resume_is_idempotent_and_completes_checkpoint(self):
        first = FakeClient([self.page_one, NextERPServerError("indisponível")])
        with self.assertRaises(NextERPServerError):
            WarehouseSynchronizer(first).run()

        final_page = DatasetPage(
            records=[{
                "name": "WH-001", "warehouse_name": "Central Atualizado",
                "project_id": "P-01", "modified": "2026-08-28T11:00:00Z",
            }],
            next_cursor="",
            has_more=False,
            contract_version="v1",
            checkpoint=datetime(2026, 8, 28, 10, 5, tzinfo=dt_timezone.utc),
        )
        resumed = FakeClient([final_page])
        run = WarehouseSynchronizer(resumed).run()

        self.assertEqual(resumed.calls[0][1], "cursor-2")
        self.assertEqual(Warehouse.objects.count(), 1)
        self.assertEqual(IntegrationStagingRecord.objects.count(), 1)
        self.assertEqual(Warehouse.objects.get().warehouse_name, "Central Atualizado")
        checkpoint = IntegrationCheckpoint.objects.get(dataset="warehouses")
        self.assertEqual(checkpoint.resume_cursor, "")
        self.assertIsNotNone(checkpoint.completed_through)
        self.assertEqual(checkpoint.completed_through, final_page.checkpoint)
        self.assertEqual(run.status, "succeeded")
