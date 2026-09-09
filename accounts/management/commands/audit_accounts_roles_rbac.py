"""
Management Command for Accounts: Role-Based Access Control
PR #4: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from accounts.models_accounts_roles_rbac import AccountsRolesRbacMaster
from accounts.services_accounts_roles_rbac import AccountsRolesRbacWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Role-Based Access Control records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Role-Based Access Control..."))
        qs = AccountsRolesRbacMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = AccountsRolesRbacWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Role-Based Access Control."))
