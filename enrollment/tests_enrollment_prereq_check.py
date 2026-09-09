"""
Automated Test Suite for Enrollment: Prerequisite Enforcement
PR #29: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from enrollment.models_enrollment_prereq_check import EnrollmentPrereqCheckMaster, EnrollmentPrereqCheckConfiguration, EnrollmentPrereqCheckAuditTransaction
from enrollment.services_enrollment_prereq_check import EnrollmentPrereqCheckWorkflowService, EnrollmentPrereqCheckCalculationEngine, EnrollmentPrereqCheckValidationPolicyEngine
from enrollment.forms_enrollment_prereq_check import EnrollmentPrereqCheckMasterForm
from enrollment.serializers_enrollment_prereq_check import EnrollmentPrereqCheckMasterDTO

class EnrollmentPrereqCheckModelTestCase(TestCase):
    def setUp(self):
        self.record = EnrollmentPrereqCheckMaster.objects.create(
            code="ENROLLMENT_PREREQ_CHECK-TEST-01",
            name="Test EnrollmentPrereqCheck Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "ENROLLMENT_PREREQ_CHECK-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("ENROLLMENT_PREREQ_CHECK-TEST-01", str(self.record))

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

class EnrollmentPrereqCheckServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = EnrollmentPrereqCheckWorkflowService.provision_master_entity(
            code="ENROLLMENT_PREREQ_CHECK-SRV-01",
            name="Service Created EnrollmentPrereqCheck",
            capacity=80
        )
        self.assertEqual(item.code, "ENROLLMENT_PREREQ_CHECK-SRV-01")
        self.assertEqual(EnrollmentPrereqCheckMaster.objects.count(), 1)
        self.assertEqual(EnrollmentPrereqCheckConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = EnrollmentPrereqCheckWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = EnrollmentPrereqCheckWorkflowService.provision_master_entity(
            code="ENROLLMENT_PREREQ_CHECK-TR-01",
            name="Transition Test Entity"
        )
        updated = EnrollmentPrereqCheckWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = EnrollmentPrereqCheckWorkflowService.provision_master_entity(
            code="ENROLLMENT_PREREQ_CHECK-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        EnrollmentPrereqCheckWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class EnrollmentPrereqCheckFormTestCase(TestCase):
    def test_form_validation(self):
        form = EnrollmentPrereqCheckMasterForm(data={
            "code": "ENROLLMENT_PREREQ_CHECK-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class EnrollmentPrereqCheckDTOTestCase(TestCase):
    def setUp(self):
        self.record = EnrollmentPrereqCheckMaster.objects.create(
            code="ENROLLMENT_PREREQ_CHECK-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = EnrollmentPrereqCheckMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "ENROLLMENT_PREREQ_CHECK-DTO-01")

class EnrollmentPrereqCheckViewTestCase(TestCase):
    def setUp(self):
        self.record = EnrollmentPrereqCheckMaster.objects.create(
            code="ENROLLMENT_PREREQ_CHECK-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("enrollment:enrollment_prereq_check_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("enrollment:enrollment_prereq_check_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("enrollment:enrollment_prereq_check_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("enrollment:enrollment_prereq_check_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
