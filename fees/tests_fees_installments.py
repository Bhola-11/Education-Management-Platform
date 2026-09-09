"""
Automated Test Suite for Fees: Installment Plans
PR #60: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from fees.models_fees_installments import FeesInstallmentsMaster, FeesInstallmentsConfiguration, FeesInstallmentsAuditTransaction
from fees.services_fees_installments import FeesInstallmentsWorkflowService, FeesInstallmentsCalculationEngine, FeesInstallmentsValidationPolicyEngine
from fees.forms_fees_installments import FeesInstallmentsMasterForm
from fees.serializers_fees_installments import FeesInstallmentsMasterDTO

class FeesInstallmentsModelTestCase(TestCase):
    def setUp(self):
        self.record = FeesInstallmentsMaster.objects.create(
            code="FEES_INSTALLMENTS-TEST-01",
            name="Test FeesInstallments Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "FEES_INSTALLMENTS-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("FEES_INSTALLMENTS-TEST-01", str(self.record))

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

class FeesInstallmentsServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = FeesInstallmentsWorkflowService.provision_master_entity(
            code="FEES_INSTALLMENTS-SRV-01",
            name="Service Created FeesInstallments",
            capacity=80
        )
        self.assertEqual(item.code, "FEES_INSTALLMENTS-SRV-01")
        self.assertEqual(FeesInstallmentsMaster.objects.count(), 1)
        self.assertEqual(FeesInstallmentsConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = FeesInstallmentsWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = FeesInstallmentsWorkflowService.provision_master_entity(
            code="FEES_INSTALLMENTS-TR-01",
            name="Transition Test Entity"
        )
        updated = FeesInstallmentsWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = FeesInstallmentsWorkflowService.provision_master_entity(
            code="FEES_INSTALLMENTS-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        FeesInstallmentsWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class FeesInstallmentsFormTestCase(TestCase):
    def test_form_validation(self):
        form = FeesInstallmentsMasterForm(data={
            "code": "FEES_INSTALLMENTS-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class FeesInstallmentsDTOTestCase(TestCase):
    def setUp(self):
        self.record = FeesInstallmentsMaster.objects.create(
            code="FEES_INSTALLMENTS-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = FeesInstallmentsMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "FEES_INSTALLMENTS-DTO-01")

class FeesInstallmentsViewTestCase(TestCase):
    def setUp(self):
        self.record = FeesInstallmentsMaster.objects.create(
            code="FEES_INSTALLMENTS-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("fees:fees_installments_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("fees:fees_installments_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("fees:fees_installments_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("fees:fees_installments_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
