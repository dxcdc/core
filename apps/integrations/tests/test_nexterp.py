from unittest.mock import Mock

import requests
from django.test import SimpleTestCase

from apps.integrations.services.nexterp import (
    NextERPAnalyticsClient,
    NextERPAuthenticationError,
    NextERPContractError,
    NextERPRateLimitError,
)


class NextERPClientTests(SimpleTestCase):
    def make_client(self, responses, max_retries=0):
        session = Mock()
        session.get.side_effect = responses
        return NextERPAnalyticsClient(
            base_url="https://erp.example.test",
            api_key="api-key",
            api_secret="api-secret",
            max_retries=max_retries,
            session=session,
            sleeper=lambda _: None,
        ), session

    @staticmethod
    def response(status, payload=None):
        response = Mock(status_code=status)
        response.json.return_value = payload
        return response

    def test_validates_v1_page_and_uses_server_only_token(self):
        client, session = self.make_client([
            self.response(200, {"message": {
                "contract_version": "v1",
                "data": [{"name": "WH-001", "modified": "2026-08-28T10:00:00Z"}],
                "has_more": False,
                "next_cursor": None,
                "checkpoint": "2026-08-28T10:05:00Z",
            }})
        ])
        page = client.fetch_dataset_page("warehouses")
        self.assertEqual(page.records[0]["name"], "WH-001")
        headers = session.get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "token api-key:api-secret")

    def test_rejects_contract_other_than_v1(self):
        client, _ = self.make_client([
            self.response(200, {
                "contract_version": "v2", "data": [], "has_more": False,
                "checkpoint": "2026-08-28T10:05:00Z",
            })
        ])
        with self.assertRaisesRegex(NextERPContractError, "esperado v1"):
            client.fetch_dataset_page("warehouses")

    def test_separates_authentication_error(self):
        client, _ = self.make_client([self.response(401)])
        with self.assertRaises(NextERPAuthenticationError):
            client.fetch_dataset_page("warehouses")

    def test_retries_429_then_reports_rate_limit(self):
        client, session = self.make_client(
            [self.response(429), self.response(429)], max_retries=1
        )
        with self.assertRaises(NextERPRateLimitError):
            client.fetch_dataset_page("warehouses")
        self.assertEqual(session.get.call_count, 2)

    def test_catalog_requires_read_only_warehouses(self):
        client, _ = self.make_client([self.response(200, {"message": {
            "contract_version": "v1",
            "datasets": [{"id": "warehouses", "read_only": True, "records": 3}],
        }})])
        catalog = client.fetch_catalog()
        self.assertEqual(catalog["datasets"][0]["records"], 3)

    def test_fetches_persisted_ongsys_warehouse_mappings(self):
        client, session = self.make_client([self.response(200, {"message": [{
            "cost_center_code": "CC-01",
            "description": "Centro confirmado",
            "warehouse": "Armazem Central - C",
            "warehouse_status": "Ativo",
            "status": "Ativo",
            "enabled": 1,
        }]})])

        mappings = client.fetch_ongsys_warehouse_mappings()

        self.assertEqual("CC-01", mappings[0]["cost_center_code"])
        self.assertEqual(client.ongsys_mappings_path, session.get.call_args.args[0].replace(client.base_url, ""))

    def test_rejects_incomplete_ongsys_warehouse_mapping(self):
        client, _ = self.make_client([self.response(200, {"message": [{
            "warehouse": "Armazem Central - C",
            "warehouse_status": "Ativo",
            "status": "Ativo",
        }]})])

        with self.assertRaisesRegex(NextERPContractError, "sem centro de custo"):
            client.fetch_ongsys_warehouse_mappings()
