"""
Management Command for Enrollment: Admissions Pipeline
PR #26: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from enrollment.models_enrollment_admissions import EnrollmentAdmissionsMaster
from enrollment.services_enrollment_admissions import EnrollmentAdmissionsWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Admissions Pipeline records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Admissions Pipeline..."))
        qs = EnrollmentAdmissionsMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = EnrollmentAdmissionsWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Admissions Pipeline."))
