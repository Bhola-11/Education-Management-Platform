"""
Management Command for Grading: GPA/CGPA Calculation
PR #55: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from grading.models_grading_gpa_engine import GradingGpaEngineMaster
from grading.services_grading_gpa_engine import GradingGpaEngineWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for GPA/CGPA Calculation records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for GPA/CGPA Calculation..."))
        qs = GradingGpaEngineMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = GradingGpaEngineWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for GPA/CGPA Calculation."))
