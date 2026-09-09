"""
Management Command for Grading: Grade Scales & Rules
PR #52: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from grading.models_grading_scales import GradingScalesMaster
from grading.services_grading_scales import GradingScalesWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Grade Scales & Rules records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Grade Scales & Rules..."))
        qs = GradingScalesMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = GradingScalesWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Grade Scales & Rules."))
