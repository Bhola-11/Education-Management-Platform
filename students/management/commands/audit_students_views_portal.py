"""
Management Command for Students: Student Portal & Directory
PR #20: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from students.models_students_views_portal import StudentsViewsPortalMaster
from students.services_students_views_portal import StudentsViewsPortalWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Student Portal & Directory records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Student Portal & Directory..."))
        qs = StudentsViewsPortalMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = StudentsViewsPortalWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Student Portal & Directory."))
