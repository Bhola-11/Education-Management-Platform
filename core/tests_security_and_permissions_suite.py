"""
Automated Test Suite for Core: Security & Penetration Tests
PR #99: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from core.models_security_and_permissions_suite import SecurityAndPermissionsSuiteMaster, SecurityAndPermissionsSuiteConfiguration, SecurityAndPermissionsSuiteAuditTransaction
from core.services_security_and_permissions_suite import SecurityAndPermissionsSuiteWorkflowService, SecurityAndPermissionsSuiteCalculationEngine, SecurityAndPermissionsSuiteValidationPolicyEngine
from core.forms_security_and_permissions_suite import SecurityAndPermissionsSuiteMasterForm
from core.serializers_security_and_permissions_suite import SecurityAndPermissionsSuiteMasterDTO

class SecurityAndPermissionsSuiteModelTestCase(TestCase):
    def setUp(self):
        self.record = SecurityAndPermissionsSuiteMaster.objects.create(
            code="SECURITY_AND_PERMISSIONS_SUITE-TEST-01",
            name="Test SecurityAndPermissionsSuite Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "SECURITY_AND_PERMISSIONS_SUITE-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("SECURITY_AND_PERMISSIONS_SUITE-TEST-01", str(self.record))

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

class SecurityAndPermissionsSuiteServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = SecurityAndPermissionsSuiteWorkflowService.provision_master_entity(
            code="SECURITY_AND_PERMISSIONS_SUITE-SRV-01",
            name="Service Created SecurityAndPermissionsSuite",
            capacity=80
        )
        self.assertEqual(item.code, "SECURITY_AND_PERMISSIONS_SUITE-SRV-01")
        self.assertEqual(SecurityAndPermissionsSuiteMaster.objects.count(), 1)
        self.assertEqual(SecurityAndPermissionsSuiteConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = SecurityAndPermissionsSuiteWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = SecurityAndPermissionsSuiteWorkflowService.provision_master_entity(
            code="SECURITY_AND_PERMISSIONS_SUITE-TR-01",
            name="Transition Test Entity"
        )
        updated = SecurityAndPermissionsSuiteWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = SecurityAndPermissionsSuiteWorkflowService.provision_master_entity(
            code="SECURITY_AND_PERMISSIONS_SUITE-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        SecurityAndPermissionsSuiteWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class SecurityAndPermissionsSuiteFormTestCase(TestCase):
    def test_form_validation(self):
        form = SecurityAndPermissionsSuiteMasterForm(data={
            "code": "SECURITY_AND_PERMISSIONS_SUITE-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class SecurityAndPermissionsSuiteDTOTestCase(TestCase):
    def setUp(self):
        self.record = SecurityAndPermissionsSuiteMaster.objects.create(
            code="SECURITY_AND_PERMISSIONS_SUITE-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = SecurityAndPermissionsSuiteMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "SECURITY_AND_PERMISSIONS_SUITE-DTO-01")

class SecurityAndPermissionsSuiteViewTestCase(TestCase):
    def setUp(self):
        self.record = SecurityAndPermissionsSuiteMaster.objects.create(
            code="SECURITY_AND_PERMISSIONS_SUITE-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("core:security_and_permissions_suite_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("core:security_and_permissions_suite_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("core:security_and_permissions_suite_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("core:security_and_permissions_suite_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
