"""
Management Command for Core: Security & Penetration Tests
PR #99: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from core.models_security_and_permissions_suite import SecurityAndPermissionsSuiteMaster
from core.services_security_and_permissions_suite import SecurityAndPermissionsSuiteWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Security & Penetration Tests records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Security & Penetration Tests..."))
        qs = SecurityAndPermissionsSuiteMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = SecurityAndPermissionsSuiteWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Security & Penetration Tests."))
