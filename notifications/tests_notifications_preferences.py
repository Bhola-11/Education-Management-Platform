"""
Automated Test Suite for Notifications: Notification Preferences
PR #79: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from notifications.models_notifications_preferences import NotificationsPreferencesMaster, NotificationsPreferencesConfiguration, NotificationsPreferencesAuditTransaction
from notifications.services_notifications_preferences import NotificationsPreferencesWorkflowService, NotificationsPreferencesCalculationEngine, NotificationsPreferencesValidationPolicyEngine
from notifications.forms_notifications_preferences import NotificationsPreferencesMasterForm
from notifications.serializers_notifications_preferences import NotificationsPreferencesMasterDTO

class NotificationsPreferencesModelTestCase(TestCase):
    def setUp(self):
        self.record = NotificationsPreferencesMaster.objects.create(
            code="NOTIFICATIONS_PREFERENCES-TEST-01",
            name="Test NotificationsPreferences Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "NOTIFICATIONS_PREFERENCES-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("NOTIFICATIONS_PREFERENCES-TEST-01", str(self.record))

    def test_utilization_calculation(self):
        util = self.record.calculate_utilization()
        self.assertEqual(util, 40.0)

    def test_allocation_increment(self):
        self.record.increment_allocation(5)
        self.assertEqual(self.record.allocated_count, 25)

    def test_composite_score_computation(self):
        score = self.record.compute_composite_score()
        self.assertGreater(score, Decimal("0.00"))

    def test_record_locking(self):
        self.record.lock_record("Test Audit Lock")
        self.assertTrue(self.record.is_locked)
        self.record.unlock_record()
        self.assertFalse(self.record.is_locked)

class NotificationsPreferencesServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = NotificationsPreferencesWorkflowService.provision_master_entity(
            code="NOTIFICATIONS_PREFERENCES-SRV-01",
            name="Service Created NotificationsPreferences",
            capacity=80
        )
        self.assertEqual(item.code, "NOTIFICATIONS_PREFERENCES-SRV-01")
        self.assertEqual(NotificationsPreferencesMaster.objects.count(), 1)
        self.assertEqual(NotificationsPreferencesConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = NotificationsPreferencesWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = NotificationsPreferencesWorkflowService.provision_master_entity(
            code="NOTIFICATIONS_PREFERENCES-TR-01",
            name="Transition Test Entity"
        )
        updated = NotificationsPreferencesWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = NotificationsPreferencesWorkflowService.provision_master_entity(
            code="NOTIFICATIONS_PREFERENCES-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        NotificationsPreferencesWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class NotificationsPreferencesFormTestCase(TestCase):
    def test_form_validation(self):
        form = NotificationsPreferencesMasterForm(data={
            "code": "NOTIFICATIONS_PREFERENCES-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class NotificationsPreferencesDTOTestCase(TestCase):
    def setUp(self):
        self.record = NotificationsPreferencesMaster.objects.create(
            code="NOTIFICATIONS_PREFERENCES-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = NotificationsPreferencesMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "NOTIFICATIONS_PREFERENCES-DTO-01")

class NotificationsPreferencesViewTestCase(TestCase):
    def setUp(self):
        self.record = NotificationsPreferencesMaster.objects.create(
            code="NOTIFICATIONS_PREFERENCES-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("notifications:notifications_preferences_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("notifications:notifications_preferences_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("notifications:notifications_preferences_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("notifications:notifications_preferences_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
