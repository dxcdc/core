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
            }})
        ])
        page = client.fetch_dataset_page("warehouses")
        self.assertEqual(page.records[0]["name"], "WH-001")
        headers = session.get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "token api-key:api-secret")

    def test_rejects_contract_other_than_v1(self):
        client, _ = self.make_client([
            self.response(200, {
                "contract_version": "v2", "data": [], "has_more": False
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
