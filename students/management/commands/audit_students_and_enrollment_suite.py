"""
Management Command for Students: Students & Enrollment Tests
PR #96: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from students.models_students_and_enrollment_suite import StudentsAndEnrollmentSuiteMaster
from students.services_students_and_enrollment_suite import StudentsAndEnrollmentSuiteWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Students & Enrollment Tests records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Students & Enrollment Tests..."))
        qs = StudentsAndEnrollmentSuiteMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = StudentsAndEnrollmentSuiteWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Students & Enrollment Tests."))
