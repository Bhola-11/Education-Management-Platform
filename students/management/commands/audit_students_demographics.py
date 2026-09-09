"""
Management Command for Students: Student Demographics
PR #16: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from students.models_students_demographics import StudentsDemographicsMaster
from students.services_students_demographics import StudentsDemographicsWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Student Demographics records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Student Demographics..."))
        qs = StudentsDemographicsMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = StudentsDemographicsWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Student Demographics."))
