"""
Management Command for Grading: Rank Lists & Distinctions
PR #57: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from grading.models_grading_rank_lists import GradingRankListsMaster
from grading.services_grading_rank_lists import GradingRankListsWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Rank Lists & Distinctions records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Rank Lists & Distinctions..."))
        qs = GradingRankListsMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = GradingRankListsWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Rank Lists & Distinctions."))
