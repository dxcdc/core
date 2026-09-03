from unittest.mock import Mock, patch

from django.test import TestCase

from apps.integrations.models import OngsysFornecedor
from apps.integrations.ongsys_sync import OngsysSyncError, sync_fornecedores


class OngsysSyncFailureTests(TestCase):
    @patch('apps.integrations.ongsys_sync.get_headers', return_value={})
    @patch('apps.integrations.ongsys_sync.requests.get')
    def test_http_failure_is_propagated_instead_of_returning_false_success(
        self, requests_get, _get_headers
    ):
        requests_get.return_value = Mock(status_code=401)

        with self.assertRaisesMessage(OngsysSyncError, 'HTTP 401 na página 1'):
            sync_fornecedores(max_pages=1)

        self.assertEqual(0, OngsysFornecedor.objects.count())

    @patch('apps.integrations.ongsys_sync.get_headers', return_value={})
    @patch('apps.integrations.ongsys_sync.requests.get')
    def test_empty_successful_page_finishes_without_error(
        self, requests_get, _get_headers
    ):
        requests_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={'data': []}),
        )

        result = sync_fornecedores(max_pages=1)

        self.assertEqual('Fornecedores', result['entidade'])
        self.assertEqual(0, result['total'])
