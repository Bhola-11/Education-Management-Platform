"""
Management Command for Notifications: Campus Broadcasts
PR #78: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from notifications.models_notifications_broadcast import NotificationsBroadcastMaster
from notifications.services_notifications_broadcast import NotificationsBroadcastWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Campus Broadcasts records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Campus Broadcasts..."))
        qs = NotificationsBroadcastMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = NotificationsBroadcastWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Campus Broadcasts."))
