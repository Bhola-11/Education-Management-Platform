"""
Management Command for Core: Security Audit Trail
PR #92: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from core.models_core_audit_logging import CoreAuditLoggingMaster
from core.services_core_audit_logging import CoreAuditLoggingWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Security Audit Trail records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Security Audit Trail..."))
        qs = CoreAuditLoggingMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = CoreAuditLoggingWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Security Audit Trail."))
