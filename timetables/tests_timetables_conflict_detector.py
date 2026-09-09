"""
Automated Test Suite for Timetables: Schedule Conflict Solver
PR #33: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from timetables.models_timetables_conflict_detector import TimetablesConflictDetectorMaster, TimetablesConflictDetectorConfiguration, TimetablesConflictDetectorAuditTransaction
from timetables.services_timetables_conflict_detector import TimetablesConflictDetectorWorkflowService, TimetablesConflictDetectorCalculationEngine, TimetablesConflictDetectorValidationPolicyEngine
from timetables.forms_timetables_conflict_detector import TimetablesConflictDetectorMasterForm
from timetables.serializers_timetables_conflict_detector import TimetablesConflictDetectorMasterDTO

class TimetablesConflictDetectorModelTestCase(TestCase):
    def setUp(self):
        self.record = TimetablesConflictDetectorMaster.objects.create(
            code="TIMETABLES_CONFLICT_DETECTOR-TEST-01",
            name="Test TimetablesConflictDetector Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "TIMETABLES_CONFLICT_DETECTOR-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("TIMETABLES_CONFLICT_DETECTOR-TEST-01", str(self.record))

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

class TimetablesConflictDetectorServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = TimetablesConflictDetectorWorkflowService.provision_master_entity(
            code="TIMETABLES_CONFLICT_DETECTOR-SRV-01",
            name="Service Created TimetablesConflictDetector",
            capacity=80
        )
        self.assertEqual(item.code, "TIMETABLES_CONFLICT_DETECTOR-SRV-01")
        self.assertEqual(TimetablesConflictDetectorMaster.objects.count(), 1)
        self.assertEqual(TimetablesConflictDetectorConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = TimetablesConflictDetectorWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = TimetablesConflictDetectorWorkflowService.provision_master_entity(
            code="TIMETABLES_CONFLICT_DETECTOR-TR-01",
            name="Transition Test Entity"
        )
        updated = TimetablesConflictDetectorWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = TimetablesConflictDetectorWorkflowService.provision_master_entity(
            code="TIMETABLES_CONFLICT_DETECTOR-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        TimetablesConflictDetectorWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class TimetablesConflictDetectorFormTestCase(TestCase):
    def test_form_validation(self):
        form = TimetablesConflictDetectorMasterForm(data={
            "code": "TIMETABLES_CONFLICT_DETECTOR-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class TimetablesConflictDetectorDTOTestCase(TestCase):
    def setUp(self):
        self.record = TimetablesConflictDetectorMaster.objects.create(
            code="TIMETABLES_CONFLICT_DETECTOR-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = TimetablesConflictDetectorMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "TIMETABLES_CONFLICT_DETECTOR-DTO-01")

class TimetablesConflictDetectorViewTestCase(TestCase):
    def setUp(self):
        self.record = TimetablesConflictDetectorMaster.objects.create(
            code="TIMETABLES_CONFLICT_DETECTOR-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("timetables:timetables_conflict_detector_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("timetables:timetables_conflict_detector_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("timetables:timetables_conflict_detector_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("timetables:timetables_conflict_detector_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
