"""
Automated Test Suite for Teachers: Faculty Workload
PR #24: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from teachers.models_teachers_workload import TeachersWorkloadMaster, TeachersWorkloadConfiguration, TeachersWorkloadAuditTransaction
from teachers.services_teachers_workload import TeachersWorkloadWorkflowService, TeachersWorkloadCalculationEngine, TeachersWorkloadValidationPolicyEngine
from teachers.forms_teachers_workload import TeachersWorkloadMasterForm
from teachers.serializers_teachers_workload import TeachersWorkloadMasterDTO

class TeachersWorkloadModelTestCase(TestCase):
    def setUp(self):
        self.record = TeachersWorkloadMaster.objects.create(
            code="TEACHERS_WORKLOAD-TEST-01",
            name="Test TeachersWorkload Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "TEACHERS_WORKLOAD-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("TEACHERS_WORKLOAD-TEST-01", str(self.record))

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

class TeachersWorkloadServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = TeachersWorkloadWorkflowService.provision_master_entity(
            code="TEACHERS_WORKLOAD-SRV-01",
            name="Service Created TeachersWorkload",
            capacity=80
        )
        self.assertEqual(item.code, "TEACHERS_WORKLOAD-SRV-01")
        self.assertEqual(TeachersWorkloadMaster.objects.count(), 1)
        self.assertEqual(TeachersWorkloadConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = TeachersWorkloadWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = TeachersWorkloadWorkflowService.provision_master_entity(
            code="TEACHERS_WORKLOAD-TR-01",
            name="Transition Test Entity"
        )
        updated = TeachersWorkloadWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = TeachersWorkloadWorkflowService.provision_master_entity(
            code="TEACHERS_WORKLOAD-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        TeachersWorkloadWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class TeachersWorkloadFormTestCase(TestCase):
    def test_form_validation(self):
        form = TeachersWorkloadMasterForm(data={
            "code": "TEACHERS_WORKLOAD-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class TeachersWorkloadDTOTestCase(TestCase):
    def setUp(self):
        self.record = TeachersWorkloadMaster.objects.create(
            code="TEACHERS_WORKLOAD-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = TeachersWorkloadMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "TEACHERS_WORKLOAD-DTO-01")

class TeachersWorkloadViewTestCase(TestCase):
    def setUp(self):
        self.record = TeachersWorkloadMaster.objects.create(
            code="TEACHERS_WORKLOAD-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("teachers:teachers_workload_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("teachers:teachers_workload_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("teachers:teachers_workload_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("teachers:teachers_workload_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
