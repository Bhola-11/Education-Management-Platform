import pytest
from django.test import TestCase
from django.apps import apps

class ModelsIntegrityTestSuite(TestCase):
    def test_all_models_registered(self):
        all_models = apps.get_models()
        self.assertGreater(len(all_models), 100)

    def test_database_connection(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1;')
            row = cursor.fetchone()
            self.assertEqual(row[0], 1)
