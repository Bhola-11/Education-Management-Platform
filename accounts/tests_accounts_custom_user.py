"""
Automated Test Suite for Accounts: Authentication
PR #3: Unit, Integration, Model, Form, and Service Assertions.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models_accounts_custom_user import AccountsCustomUserMaster, AccountsCustomUserConfiguration, AccountsCustomUserAuditTransaction
from accounts.services_accounts_custom_user import AccountsCustomUserWorkflowService, AccountsCustomUserCalculationEngine, AccountsCustomUserValidationPolicyEngine
from accounts.forms_accounts_custom_user import AccountsCustomUserMasterForm
from accounts.serializers_accounts_custom_user import AccountsCustomUserMasterDTO

class AccountsCustomUserModelTestCase(TestCase):
    def setUp(self):
        self.record = AccountsCustomUserMaster.objects.create(
            code="ACCOUNTS_CUSTOM_USER-TEST-01",
            name="Test AccountsCustomUser Instance",
            description="Testing master model constraints.",
            capacity_limit=50,
            allocated_count=20,
            monetary_value=Decimal("150.00"),
            score_rating=Decimal("4.50"),
            is_active=True
        )

    def test_record_attributes(self):
        self.assertEqual(self.record.code, "ACCOUNTS_CUSTOM_USER-TEST-01")
        self.assertTrue(self.record.is_active)
        self.assertEqual(self.record.capacity_limit, 50)
        self.assertIn("ACCOUNTS_CUSTOM_USER-TEST-01", str(self.record))

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

class AccountsCustomUserServiceTestCase(TestCase):
    def test_provision_workflow(self):
        item = AccountsCustomUserWorkflowService.provision_master_entity(
            code="ACCOUNTS_CUSTOM_USER-SRV-01",
            name="Service Created AccountsCustomUser",
            capacity=80
        )
        self.assertEqual(item.code, "ACCOUNTS_CUSTOM_USER-SRV-01")
        self.assertEqual(AccountsCustomUserMaster.objects.count(), 1)
        self.assertEqual(AccountsCustomUserConfiguration.objects.count(), 1)

    def test_kpi_computation(self):
        kpis = AccountsCustomUserWorkflowService.calculate_domain_kpis()
        self.assertIn("total_records", kpis)
        self.assertIn("total_monetary_value", kpis)

    def test_state_transition(self):
        item = AccountsCustomUserWorkflowService.provision_master_entity(
            code="ACCOUNTS_CUSTOM_USER-TR-01",
            name="Transition Test Entity"
        )
        updated = AccountsCustomUserWorkflowService.execute_state_transition(item.id, "ACTIVE")
        self.assertEqual(updated.status, "ACTIVE")

    def test_capacity_allocation(self):
        item = AccountsCustomUserWorkflowService.provision_master_entity(
            code="ACCOUNTS_CUSTOM_USER-CAP-01",
            name="Capacity Test Entity",
            capacity=10
        )
        AccountsCustomUserWorkflowService.allocate_resource_capacity(item.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.allocated_count, 5)

class AccountsCustomUserFormTestCase(TestCase):
    def test_form_validation(self):
        form = AccountsCustomUserMasterForm(data={
            "code": "ACCOUNTS_CUSTOM_USER-FM-01",
            "name": "Form Valid Entity",
            "capacity_limit": 100,
            "allocated_count": 10,
            "monetary_value": "250.00",
            "score_rating": "4.20",
            "is_active": True
        })
        self.assertTrue(form.is_valid())

class AccountsCustomUserDTOTestCase(TestCase):
    def setUp(self):
        self.record = AccountsCustomUserMaster.objects.create(
            code="ACCOUNTS_CUSTOM_USER-DTO-01",
            name="DTO Master Entity"
        )

    def test_serialization(self):
        dto = AccountsCustomUserMasterDTO(self.record)
        data = dto.to_dict()
        self.assertEqual(data["code"], "ACCOUNTS_CUSTOM_USER-DTO-01")

class AccountsCustomUserViewTestCase(TestCase):
    def setUp(self):
        self.record = AccountsCustomUserMaster.objects.create(
            code="ACCOUNTS_CUSTOM_USER-VW-01",
            name="View Testing Record"
        )

    def test_list_endpoint(self):
        url = reverse("accounts:accounts_custom_user_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_detail_endpoint(self):
        url = reverse("accounts:accounts_custom_user_detail", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_print_endpoint(self):
        url = reverse("accounts:accounts_custom_user_print", kwargs={"pk": self.record.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_analytics_endpoint(self):
        url = reverse("accounts:accounts_custom_user_analytics")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
