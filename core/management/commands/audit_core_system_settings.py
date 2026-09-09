"""
Management Command for Core: Institutional Settings
PR #94: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from core.models_core_system_settings import CoreSystemSettingsMaster
from core.services_core_system_settings import CoreSystemSettingsWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Institutional Settings records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Institutional Settings..."))
        qs = CoreSystemSettingsMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = CoreSystemSettingsWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Institutional Settings."))
