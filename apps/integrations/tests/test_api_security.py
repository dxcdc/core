import os
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class ExistingM2MSecurityTests(TestCase):
    def test_missing_key_is_denied(self):
        with patch.dict(os.environ, {"INTERNAL_M2M_API_KEY": "server-secret"}):
            response = self.client.get(reverse("dashboard:api_auth_verify"))
        self.assertEqual(response.status_code, 401)

    def test_workspace_response_never_echoes_key(self):
        with patch.dict(os.environ, {"INTERNAL_M2M_API_KEY": "server-secret"}):
            response = self.client.get(
                reverse("dashboard:api_workspace_data"),
                HTTP_X_API_KEY="server-secret",
            )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("server-secret", response.content.decode())
