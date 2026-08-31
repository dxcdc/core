from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.dashboard.views import _get_official_ongsys_warehouse_mappings
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
