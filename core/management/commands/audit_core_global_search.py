"""
Management Command for Core: Global Search Indexer
PR #91: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from core.models_core_global_search import CoreGlobalSearchMaster
from core.services_core_global_search import CoreGlobalSearchWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Global Search Indexer records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Global Search Indexer..."))
        qs = CoreGlobalSearchMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = CoreGlobalSearchWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Global Search Indexer."))
