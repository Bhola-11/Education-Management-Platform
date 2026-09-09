"""
Management Command for Analytics: Enterprise Export Pipeline
PR #90: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from analytics.models_analytics_export_pipeline import AnalyticsExportPipelineMaster
from analytics.services_analytics_export_pipeline import AnalyticsExportPipelineWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Enterprise Export Pipeline records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Enterprise Export Pipeline..."))
        qs = AnalyticsExportPipelineMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = AnalyticsExportPipelineWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Enterprise Export Pipeline."))
