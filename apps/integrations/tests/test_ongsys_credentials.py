import base64

from django.test import SimpleTestCase, override_settings

from apps.integrations.ongsys_credentials import (
    OngsysCredentialsError,
    get_ongsys_credentials,
    get_ongsys_headers,
)


class OngsysCredentialsTests(SimpleTestCase):
    @override_settings(
        ONGSYS_USERNAME="03.970.166/0001-29",
        ONGSYS_PASSWORD="test-only-password",
        ONGSYS_URL_BASE="https://example.invalid/api/v2/",
    )
    def test_builds_basic_auth_from_standardized_settings(self):
        credentials = get_ongsys_credentials()

        self.assertEqual("03970166000129", credentials.username)
        self.assertEqual("https://example.invalid/api/v2/", credentials.base_url)
        expected = base64.b64encode(
            b"03970166000129:test-only-password"
        ).decode("ascii")
        self.assertEqual(f"Basic {expected}", get_ongsys_headers()["Authorization"])

    @override_settings(
        ONGSYS_USERNAME="",
        ONGSYS_PASSWORD="",
        ONGSYS_URL_BASE="https://example.invalid/api/v2/",
    )
    def test_fails_closed_without_credentials(self):
        with self.assertRaisesRegex(OngsysCredentialsError, "não configurada"):
            get_ongsys_headers()
