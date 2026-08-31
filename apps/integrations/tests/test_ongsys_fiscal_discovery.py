from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.integrations.ongsys_fiscal_discovery import (
    OngsysFiscalDiscoveryError,
    discover_fiscal_endpoint,
)


@override_settings(
    ONGSYS_USERNAME="03970166000129",
    ONGSYS_PASSWORD="test-only-password",
    ONGSYS_URL_BASE="https://ongsys.example/api/v2/",
)
class OngsysFiscalDiscoveryTests(SimpleTestCase):
    def response(self, status, payload):
        response = Mock(status_code=status)
        response.json.return_value = payload
        return response

    def test_discovers_schema_without_returning_values(self):
        session = Mock()
        session.get.return_value = self.response(
            200,
            {"data": [{"idNota": 987, "fornecedor": {"nome": "Sigiloso"}}]},
        )

        result = discover_fiscal_endpoint(
            "nfe", "2026-08-01", "2026-08-31", session=session
        )

        self.assertEqual("notas-produto", result.endpoint)
        self.assertEqual(1, result.records_seen)
        self.assertEqual(
            {"idNota": "integer", "fornecedor": {"nome": "string"}},
            result.record_shape,
        )
        serialized = str(result.as_dict())
        self.assertNotIn("Sigiloso", serialized)
        self.assertNotIn("987", serialized)

    def test_sends_required_date_and_page_filters(self):
        session = Mock()
        session.get.return_value = self.response(200, {"data": []})
        discover_fiscal_endpoint(
            "nfse", "2026-08-01", "2026-08-02", session=session
        )
        self.assertEqual(
            {
                "data_inicio": "2026-08-01",
                "data_fim": "2026-08-02",
                "pageNumber": 1,
            },
            session.get.call_args.kwargs["params"],
        )

    def test_http_error_fails_without_response_body(self):
        session = Mock()
        session.get.return_value = self.response(403, {"secret": "never-log"})
        with self.assertRaisesRegex(OngsysFiscalDiscoveryError, "HTTP 403") as error:
            discover_fiscal_endpoint(
                "nfe", "2026-08-01", "2026-08-31", session=session
            )
        self.assertNotIn("never-log", str(error.exception))

    def test_rejects_invalid_date_window_before_request(self):
        with self.assertRaisesRegex(OngsysFiscalDiscoveryError, "posterior"):
            discover_fiscal_endpoint("nfse", "2026-09-01", "2026-08-01")
