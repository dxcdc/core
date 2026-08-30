import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings import database_config


class DatabaseConfigTests(SimpleTestCase):
    def test_empty_url_keeps_local_sqlite_fallback(self):
        config = database_config('')

        self.assertEqual(config['ENGINE'], 'django.db.backends.sqlite3')

    @mock.patch.dict(os.environ, {'DATABASE_CONN_MAX_AGE': '120'})
    def test_postgres_url_is_decoded_and_options_are_preserved(self):
        config = database_config(
            'postgresql://core%20user:p%40ss@db.internal:5433/core%2Ddb?sslmode=require'
        )

        self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(config['NAME'], 'core-db')
        self.assertEqual(config['USER'], 'core user')
        self.assertEqual(config['PASSWORD'], 'p@ss')
        self.assertEqual(config['HOST'], 'db.internal')
        self.assertEqual(config['PORT'], '5433')
        self.assertEqual(config['CONN_MAX_AGE'], 120)
        self.assertEqual(config['OPTIONS'], {'sslmode': 'require'})

    def test_invalid_scheme_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            database_config('mysql://user:pass@db/core')
