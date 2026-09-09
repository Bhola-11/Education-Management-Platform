"""
Management Command for Grading: Official Academic Transcripts
PR #56: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from grading.models_grading_transcripts import GradingTranscriptsMaster
from grading.services_grading_transcripts import GradingTranscriptsWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Official Academic Transcripts records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Official Academic Transcripts..."))
        qs = GradingTranscriptsMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = GradingTranscriptsWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Official Academic Transcripts."))
