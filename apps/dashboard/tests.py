from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
