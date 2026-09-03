from pathlib import Path
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.dashboard.views import _get_official_ongsys_warehouse_mappings
from apps.integrations.models import OngsysEndpointStatus, OngsysTask
from apps.integrations.services.nexterp import NextERPConfigurationError


class SidebarNavigationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='sidebar-test',
            password='test-password',
        )
        self.client.force_login(self.user)

    def test_authenticated_dashboard_renders_all_sidebar_groups_and_items(self):
        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-cdc-submenu="cdcSubModulos"')
        self.assertContains(response, 'Google Workspace')
        self.assertContains(response, 'Infra & Docker')
        self.assertContains(response, 'Diretrizes & ADRs')
        self.assertContains(response, 'Painel Conectores')
        self.assertContains(response, 'class="cdc-logo-icon"', count=1)
        # O único ícone de casa restante pertence à barra superior, não à sidebar.
        self.assertContains(response, 'ri-home-4-line', count=1)
        self.assertNotContains(response, 'data-bs-toggle="collapse"')


class OngsysWarehouseMappingTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.integrations.services.nexterp.NextERPAnalyticsClient")
    def test_uses_only_persisted_nexterp_mapping(self, client_class):
        client_class.return_value.fetch_ongsys_warehouse_mappings.return_value = [{
            "cost_center_code": "CC-REAL",
            "description": "Centro confirmado",
            "warehouse": "Armazem confirmado - C",
            "warehouse_status": "Ativo",
            "status": "Ativo",
            "enabled": 1,
            "evidence_order_id": "12345",
            "confidence": 100,
            "validation_detail": "Correspondência exata.",
        }]

        result = _get_official_ongsys_warehouse_mappings()

        self.assertTrue(result["available"])
        self.assertEqual("CC-REAL", result["rows"][0]["codigo"])
        self.assertEqual("Centro confirmado", result["rows"][0]["centro_custo"])
        self.assertEqual("Ativo", result["rows"][0]["armazem_status"])
        self.assertEqual("12345", result["rows"][0]["evidencia"])
        self.assertTrue(result["rows"][0]["ativo"])

    @patch("apps.integrations.services.nexterp.NextERPAnalyticsClient")
    def test_reports_unavailability_without_fixture_fallback(self, client_class):
        client_class.side_effect = NextERPConfigurationError("ausente")

        result = _get_official_ongsys_warehouse_mappings()

        self.assertFalse(result["available"])
        self.assertEqual([], result["rows"])

    def test_view_contains_no_fixed_mapping_or_embedded_ongsys_key(self):
        source = Path(__file__).with_name("views.py").read_text(encoding="utf-8")
        self.assertNotIn("centros_custo_armazens = [", source)
        legacy_key = "fa009965" + "195f9770db49a9111570b531"
        self.assertNotIn(legacy_key, source)

    def test_mapping_template_has_search_and_combined_filters(self):
        template = (
            Path(__file__).resolve().parents[2]
            / "templates/dashboard/ongsys_integration.html"
        ).read_text(encoding="utf-8")
        self.assertIn('id="mappingSearchInput"', template)
        self.assertIn('id="mappingWarehouseFilter"', template)
        self.assertIn('id="mappingValidationFilter"', template)
        self.assertIn('id="mappingFiltersClear"', template)
        self.assertIn('function initMappingFilters()', template)


class OngsysConnectionStatusTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='ongsys-status-test',
            password='test-password',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    @patch('apps.integrations.ongsys_credentials.get_ongsys_credentials')
    def test_configured_secret_is_not_reported_as_validated_without_test(self, resolver):
        resolver.return_value.username = '03970166000129'
        response = self.client.get(reverse('dashboard:ongsys_integration'))
        self.assertContains(response, 'Não Avaliada')
        self.assertContains(response, 'Aguardando primeiro teste')
        self.assertNotContains(response, 'Basic Auth Validado')

    def test_dashboard_rejects_credential_submission(self):
        response = self.client.post(
            reverse('dashboard:ongsys_integration'),
            {'ongsys_cnpj': '00000000000000', 'ongsys_api_key': 'never-store-me'},
        )
        self.assertEqual(405, response.status_code)
        self.assertNotIn('never-store-me', response.content.decode())


class OngsysAccessControlTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='ongsys-staff',
            password='test-password',
            is_staff=True,
            is_superuser=True,
        )
        self.regular_user = get_user_model().objects.create_user(
            username='ongsys-regular', password='test-password'
        )

    def test_anonymous_requests_are_redirected_before_ongsys_views_run(self):
        protected_urls = [
            reverse('dashboard:ongsys_integration'),
            reverse('dashboard:ongsys_trigger_sync'),
            reverse('dashboard:ongsys_api_proxy', args=['test']),
            reverse('dashboard:ongsys_async_test_all'),
            reverse('dashboard:ongsys_async_sync_db'),
            reverse('dashboard:ongsys_task_status', args=['unknown-task']),
            reverse('dashboard:ongsys_report_data'),
            reverse('dashboard:ongsys_report_pdf'),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(302, response.status_code)
                self.assertIn('/login/', response['Location'])

    def test_authenticated_non_staff_user_cannot_access_ongsys_dashboard(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse('dashboard:ongsys_integration'))

        self.assertEqual(403, response.status_code)

    def test_staff_post_without_csrf_is_rejected_before_proxy_execution(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)

        response = csrf_client.post(
            reverse('dashboard:ongsys_api_proxy', args=['test']),
            data='{"path":"fornecedores","method":"GET"}',
            content_type='application/json',
        )

        self.assertEqual(403, response.status_code)

    def test_staff_post_without_csrf_cannot_start_background_tasks(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)

        for url in [
            reverse('dashboard:ongsys_async_test_all'),
            reverse('dashboard:ongsys_async_sync_db'),
        ]:
            with self.subTest(url=url):
                response = csrf_client.post(
                    url,
                    data='{}',
                    content_type='application/json',
                )
                self.assertEqual(403, response.status_code)

    @patch('apps.dashboard.views.requests.get')
    @patch('apps.integrations.ongsys_credentials.get_ongsys_headers')
    @patch('apps.integrations.ongsys_credentials.get_ongsys_credentials')
    def test_proxy_resolves_safe_get_from_server_allowlist(
        self, credentials_resolver, headers_resolver, requests_get
    ):
        credentials_resolver.return_value.base_url = 'https://ongsys.invalid/api/v2/'
        headers_resolver.return_value = {'Authorization': 'Basic redacted'}
        requests_get.return_value = Mock(
            status_code=200,
            headers={},
            url='https://ongsys.invalid/api/v2/fornecedores?pageNumber=1',
            json=Mock(return_value={'data': []}),
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('dashboard:ongsys_api_proxy', args=['test']),
            data='{"ep_id":"fornecedores-get","path":"fornecedores",'
                 '"method":"GET","params":{"pageNumber":1}}',
            content_type='application/json',
        )

        self.assertEqual(200, response.status_code)
        requests_get.assert_called_once_with(
            'https://ongsys.invalid/api/v2/fornecedores',
            headers={'Authorization': 'Basic redacted'},
            params={'pageNumber': 1},
            timeout=30,
        )

    @patch('apps.dashboard.views.requests.get')
    def test_proxy_rejects_write_method_before_calling_ongsys(self, requests_get):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('dashboard:ongsys_api_proxy', args=['test']),
            data='{"ep_id":"fornecedores-get","path":"fornecedores",'
                 '"method":"DELETE","params":{}}',
            content_type='application/json',
        )

        self.assertEqual(400, response.status_code)
        requests_get.assert_not_called()

    @patch('apps.dashboard.views.requests.get')
    def test_proxy_rejects_unknown_parameters_before_calling_ongsys(self, requests_get):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('dashboard:ongsys_api_proxy', args=['test']),
            data='{"ep_id":"fornecedores-get","path":"fornecedores",'
                 '"method":"GET","params":{"url":"https://example.invalid"}}',
            content_type='application/json',
        )

        self.assertEqual(400, response.status_code)
        requests_get.assert_not_called()


class OngsysPermissionBoundaryTests(TestCase):
    def _user_with_permission(self, username, codename):
        user = get_user_model().objects.create_user(
            username=username, password='test-password'
        )
        user.user_permissions.add(Permission.objects.get(codename=codename))
        return user

    def test_view_permission_does_not_grant_test_sync_or_report(self):
        viewer = self._user_with_permission(
            'ongsys-viewer', 'view_ongsysendpointstatus'
        )
        self.client.force_login(viewer)

        self.assertEqual(
            200, self.client.get(reverse('dashboard:ongsys_integration')).status_code
        )
        self.assertEqual(
            403,
            self.client.get(
                reverse('dashboard:ongsys_api_proxy', args=['test'])
            ).status_code,
        )
        self.assertEqual(
            403, self.client.get(reverse('dashboard:ongsys_async_sync_db')).status_code
        )
        self.assertEqual(
            403, self.client.get(reverse('dashboard:ongsys_report_data')).status_code
        )

    def test_report_permission_grants_only_report_endpoints(self):
        reporter = self._user_with_permission(
            'ongsys-reporter', 'view_ongsys_report'
        )
        self.client.force_login(reporter)

        self.assertEqual(
            200, self.client.get(reverse('dashboard:ongsys_report_data')).status_code
        )
        self.assertEqual(
            200, self.client.get(reverse('dashboard:ongsys_report_pdf')).status_code
        )
        self.assertEqual(
            403, self.client.get(reverse('dashboard:ongsys_integration')).status_code
        )

    def test_report_uses_persisted_telemetry_without_credentials_or_fake_history(self):
        reporter = self._user_with_permission(
            'ongsys-live-reporter', 'view_ongsys_report'
        )
        OngsysEndpointStatus.objects.create(
            endpoint_id='fornecedores-get',
            endpoint_path='fornecedores',
            metodo='GET',
            ultimo_status_http=200,
            status_classificacao='success',
            latencia_ms=87,
            ultima_vez_testado=timezone.now(),
        )
        self.client.force_login(reporter)

        response = self.client.get(reverse('dashboard:ongsys_report_data'))

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(1, payload['tested_count'])
        self.assertEqual(1, payload['success_count'])
        self.assertEqual(100.0, payload['conformity_pct'])
        self.assertEqual([], payload['history'])
        serialized = response.content.decode('utf-8')
        self.assertNotIn('Credencial API', serialized)
        self.assertNotIn('f0...5e', serialized)
        self.assertNotIn('95% OPERACIONAL', serialized)

    def test_test_permission_reaches_proxy_but_not_sync(self):
        tester = self._user_with_permission('ongsys-tester', 'test_ongsys_api')
        self.client.force_login(tester)

        response = self.client.post(
            reverse('dashboard:ongsys_api_proxy', args=['test']),
            data='{"ep_id":"not-allowed","method":"GET","params":{}}',
            content_type='application/json',
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            403, self.client.get(reverse('dashboard:ongsys_async_sync_db')).status_code
        )

    def test_sync_permission_reaches_sync_view_but_not_proxy(self):
        synchronizer = self._user_with_permission(
            'ongsys-synchronizer', 'sync_ongsys_data'
        )
        self.client.force_login(synchronizer)

        self.assertEqual(
            405, self.client.get(reverse('dashboard:ongsys_async_sync_db')).status_code
        )
        self.assertEqual(
            403,
            self.client.get(
                reverse('dashboard:ongsys_api_proxy', args=['test'])
            ).status_code,
        )

    def test_sync_rejects_unknown_entity_and_unbounded_pages(self):
        synchronizer = self._user_with_permission(
            'ongsys-sync-validator', 'sync_ongsys_data'
        )
        self.client.force_login(synchronizer)

        invalid_payloads = [
            '{"entity":"unknown","pages":1}',
            '{"entity":"fornecedores","pages":0}',
            '{"entity":"fornecedores","pages":101}',
            '{"entity":"fornecedores","pages":"invalid"}',
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    reverse('dashboard:ongsys_async_sync_db'),
                    data=payload,
                    content_type='application/json',
                )
                self.assertEqual(400, response.status_code)

    def test_sync_request_is_persisted_for_external_executor(self):
        synchronizer = self._user_with_permission(
            'ongsys-sync-owner', 'sync_ongsys_data'
        )
        self.client.force_login(synchronizer)

        response = self.client.post(
            reverse('dashboard:ongsys_async_sync_db'),
            data='{"entity":"fornecedores","pages":2}',
            content_type='application/json',
        )

        self.assertEqual(202, response.status_code)
        task = OngsysTask.objects.get(pk=response.json()['task_id'])
        self.assertEqual(synchronizer, task.solicitante)
        self.assertEqual(OngsysTask.Status.QUEUED, task.status)
        self.assertEqual(2, task.paginas)

    def test_legacy_sync_url_also_queues_durable_task(self):
        synchronizer = self._user_with_permission(
            'ongsys-legacy-sync-owner', 'sync_ongsys_data'
        )
        self.client.force_login(synchronizer)

        response = self.client.post(
            reverse('dashboard:ongsys_trigger_sync'),
            data='{"entity":"clientes","pages":1}',
            content_type='application/json',
        )

        self.assertEqual(202, response.status_code)
        task = OngsysTask.objects.get(pk=response.json()['task_id'])
        self.assertEqual('clientes', task.entidade)
        self.assertEqual(OngsysTask.Status.QUEUED, task.status)

    def test_task_status_is_visible_to_owner_but_not_another_user(self):
        owner = self._user_with_permission('ongsys-task-owner', 'sync_ongsys_data')
        other = get_user_model().objects.create_user(
            username='ongsys-task-other', password='test-password'
        )
        task = OngsysTask.objects.create(
            tipo=OngsysTask.Tipo.SYNC_DB,
            solicitante=owner,
            entidade='fornecedores',
            paginas=1,
        )

        self.client.force_login(owner)
        owner_response = self.client.get(
            reverse('dashboard:ongsys_task_status', args=[task.pk])
        )
        self.assertEqual(200, owner_response.status_code)
        self.assertEqual('queued', owner_response.json()['status'])

        self.client.force_login(other)
        other_response = self.client.get(
            reverse('dashboard:ongsys_task_status', args=[task.pk])
        )
        self.assertEqual(403, other_response.status_code)
