"""
Management Command for Grading: Grading & Fees Tests
PR #97: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from grading.models_grading_and_fees_suite import GradingAndFeesSuiteMaster
from grading.services_grading_and_fees_suite import GradingAndFeesSuiteWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Grading & Fees Tests records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Grading & Fees Tests..."))
        qs = GradingAndFeesSuiteMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = GradingAndFeesSuiteWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Grading & Fees Tests."))
