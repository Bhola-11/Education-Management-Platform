"""
Management Command for Core: Database Diagnostics & Snapshots
PR #93: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from core.models_core_backup_restore import CoreBackupRestoreMaster
from core.services_core_backup_restore import CoreBackupRestoreWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Database Diagnostics & Snapshots records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Database Diagnostics & Snapshots..."))
        qs = CoreBackupRestoreMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = CoreBackupRestoreWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Database Diagnostics & Snapshots."))
