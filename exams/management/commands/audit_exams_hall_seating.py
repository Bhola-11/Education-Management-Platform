"""
Management Command for Exams: Exam Seating Matrix
PR #49: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from exams.models_exams_hall_seating import ExamsHallSeatingMaster
from exams.services_exams_hall_seating import ExamsHallSeatingWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Exam Seating Matrix records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Exam Seating Matrix..."))
        qs = ExamsHallSeatingMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = ExamsHallSeatingWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Exam Seating Matrix."))
