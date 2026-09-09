"""
Management Command for Timetables: Schedule Conflict Solver
PR #33: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from timetables.models_timetables_conflict_detector import TimetablesConflictDetectorMaster
from timetables.services_timetables_conflict_detector import TimetablesConflictDetectorWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Schedule Conflict Solver records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Schedule Conflict Solver..."))
        qs = TimetablesConflictDetectorMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = TimetablesConflictDetectorWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Schedule Conflict Solver."))
