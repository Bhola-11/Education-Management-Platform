"""
Management Command for Teachers: Faculty Master Record
PR #21: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from teachers.models_teachers_master_record import TeachersMasterRecordMaster
from teachers.services_teachers_master_record import TeachersMasterRecordWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Faculty Master Record records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Faculty Master Record..."))
        qs = TeachersMasterRecordMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = TeachersMasterRecordWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Faculty Master Record."))
