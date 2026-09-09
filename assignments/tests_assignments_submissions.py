"""
Automated Test Suite for Assignments: Student Submissions
PR #43: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from assignments.models_assignments_submissions import AssignmentsSubmissionsMaster, AssignmentsSubmissionsConfiguration, AssignmentsSubmissionsAuditTransaction
from assignments.services_assignments_submissions import AssignmentsSubmissionsWorkflowService, AssignmentsSubmissionsCalculationEngine, AssignmentsSubmissionsValidationPolicyEngine
from assignments.forms_assignments_submissions import AssignmentsSubmissionsMasterForm
from assignments.serializers_assignments_submissions import AssignmentsSubmissionsMasterDTO

class AssignmentsSubmissionsModelTestCase(TestCase):
    def setUp(self):
        self.record = AssignmentsSubmissionsMaster.objects.create(
            code="ASSIGNMENTS_SUBMISSIONS-TEST-01",
            name="Test AssignmentsSubmissions Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "ASSIGNMENTS_SUBMISSIONS-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("ASSIGNMENTS_SUBMISSIONS-TEST-01", str(self.record))

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

class AssignmentsSubmissionsServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = AssignmentsSubmissionsWorkflowService.provision_master_entity(
            code="ASSIGNMENTS_SUBMISSIONS-SRV-01",
            name="Service Created AssignmentsSubmissions",
            capacity=80
        )
        self.assertEqual(item.code, "ASSIGNMENTS_SUBMISSIONS-SRV-01")
        self.assertEqual(AssignmentsSubmissionsMaster.objects.count(), 1)
        self.assertEqual(AssignmentsSubmissionsConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = AssignmentsSubmissionsWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = AssignmentsSubmissionsWorkflowService.provision_master_entity(
            code="ASSIGNMENTS_SUBMISSIONS-TR-01",
            name="Transition Test Entity"
        )
        updated = AssignmentsSubmissionsWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = AssignmentsSubmissionsWorkflowService.provision_master_entity(
            code="ASSIGNMENTS_SUBMISSIONS-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        AssignmentsSubmissionsWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class AssignmentsSubmissionsFormTestCase(TestCase):
    def test_form_validation(self):
        form = AssignmentsSubmissionsMasterForm(data={
            "code": "ASSIGNMENTS_SUBMISSIONS-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class AssignmentsSubmissionsDTOTestCase(TestCase):
    def setUp(self):
        self.record = AssignmentsSubmissionsMaster.objects.create(
            code="ASSIGNMENTS_SUBMISSIONS-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = AssignmentsSubmissionsMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "ASSIGNMENTS_SUBMISSIONS-DTO-01")

class AssignmentsSubmissionsViewTestCase(TestCase):
    def setUp(self):
        self.record = AssignmentsSubmissionsMaster.objects.create(
            code="ASSIGNMENTS_SUBMISSIONS-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("assignments:assignments_submissions_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("assignments:assignments_submissions_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("assignments:assignments_submissions_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("assignments:assignments_submissions_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
