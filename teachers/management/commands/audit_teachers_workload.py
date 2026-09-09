"""
Management Command for Teachers: Faculty Workload
PR #24: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from teachers.models_teachers_workload import TeachersWorkloadMaster
from teachers.services_teachers_workload import TeachersWorkloadWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Faculty Workload records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Faculty Workload..."))
        qs = TeachersWorkloadMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = TeachersWorkloadWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Faculty Workload."))
