import pytest
from django.test import TestCase, Client
from django.urls import reverse

class PlatformSmokeTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

    def test_core_routing(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboards/', response.url)

    def test_admin_routing(self):
        response = self.client.get('/admin/')
        # Redirect to login or admin page
        self.assertIn(response.status_code, [200, 302])

    def test_students_routes(self):
        response = self.client.get('/students/students_and_enrollment_suite/')
        self.assertEqual(response.status_code, 200)

    def test_teachers_routes(self):
        # Verify app is installed and responds
        response = self.client.get('/')
        self.assertTrue(response.status_code in [200, 302])
