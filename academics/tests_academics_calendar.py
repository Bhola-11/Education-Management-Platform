"""
Automated Test Suite for Academics: Academic Calendar
PR #10: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from academics.models_academics_calendar import AcademicsCalendarMaster, AcademicsCalendarConfiguration, AcademicsCalendarAuditTransaction
from academics.services_academics_calendar import AcademicsCalendarWorkflowService, AcademicsCalendarCalculationEngine, AcademicsCalendarValidationPolicyEngine
from academics.forms_academics_calendar import AcademicsCalendarMasterForm
from academics.serializers_academics_calendar import AcademicsCalendarMasterDTO

class AcademicsCalendarModelTestCase(TestCase):
    def setUp(self):
        self.record = AcademicsCalendarMaster.objects.create(
            code="ACADEMICS_CALENDAR-TEST-01",
            name="Test AcademicsCalendar Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "ACADEMICS_CALENDAR-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("ACADEMICS_CALENDAR-TEST-01", str(self.record))

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

class AcademicsCalendarServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = AcademicsCalendarWorkflowService.provision_master_entity(
            code="ACADEMICS_CALENDAR-SRV-01",
            name="Service Created AcademicsCalendar",
            capacity=80
        )
        self.assertEqual(item.code, "ACADEMICS_CALENDAR-SRV-01")
        self.assertEqual(AcademicsCalendarMaster.objects.count(), 1)
        self.assertEqual(AcademicsCalendarConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = AcademicsCalendarWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = AcademicsCalendarWorkflowService.provision_master_entity(
            code="ACADEMICS_CALENDAR-TR-01",
            name="Transition Test Entity"
        )
        updated = AcademicsCalendarWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = AcademicsCalendarWorkflowService.provision_master_entity(
            code="ACADEMICS_CALENDAR-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        AcademicsCalendarWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class AcademicsCalendarFormTestCase(TestCase):
    def test_form_validation(self):
        form = AcademicsCalendarMasterForm(data={
            "code": "ACADEMICS_CALENDAR-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class AcademicsCalendarDTOTestCase(TestCase):
    def setUp(self):
        self.record = AcademicsCalendarMaster.objects.create(
            code="ACADEMICS_CALENDAR-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = AcademicsCalendarMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "ACADEMICS_CALENDAR-DTO-01")

class AcademicsCalendarViewTestCase(TestCase):
    def setUp(self):
        self.record = AcademicsCalendarMaster.objects.create(
            code="ACADEMICS_CALENDAR-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("academics:academics_calendar_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("academics:academics_calendar_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("academics:academics_calendar_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("academics:academics_calendar_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
