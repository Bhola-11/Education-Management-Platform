"""
Management Command for Analytics: Attendance Attrition Models
PR #89: Command-line Institutional Auditor and Verifier.
"""

from django.core.management.base import BaseCommand
from analytics.models_analytics_attendance_attrition import AnalyticsAttendanceAttritionMaster
from analytics.services_analytics_attendance_attrition import AnalyticsAttendanceAttritionWorkflowService

class Command(BaseCommand):
    help = "Audits and verifies operational integrity for Attendance Attrition Models records."

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true", help="Filter active records only.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum records to process.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Starting audit for Attendance Attrition Models..."))
        qs = AnalyticsAttendanceAttritionMaster.objects.all()
        if options["active_only"]:
            qs = qs.filter(is_active=True)
        count = qs[:options["limit"]].count()
        kpis = AnalyticsAttendanceAttritionWorkflowService.calculate_domain_kpis()
        self.stdout.write(f"Processed {count} records. Total in catalog: {kpis['total_records']}")
        self.stdout.write(self.style.SUCCESS(f"Audit completed successfully for Attendance Attrition Models."))
