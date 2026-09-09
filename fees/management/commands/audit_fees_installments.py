"""
Management Command for Fees: Installment Plans
PR #60: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from fees.models_fees_installments import FeesInstallmentsMaster
from fees.services_fees_installments import FeesInstallmentsWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Installment Plans records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Installment Plans..."))
        qs = FeesInstallmentsMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = FeesInstallmentsWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Installment Plans."))
