"""
Django ORM Signal Listeners for Attendance: Attendance Reporting
PR #41: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_reports import AttendanceReportsMaster, AttendanceReportsAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_reports")

@receiver(post_save, sender=AttendanceReportsMaster)
def log_attendance_reports_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendanceReportsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendanceReports [{instance.id}] was {action}")
    AttendanceReportsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendanceReportsMaster)
def log_attendance_reports_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendanceReports [{instance.id}] deletion requested.")
