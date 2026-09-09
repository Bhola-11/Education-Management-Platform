"""
Django ORM Signal Listeners for Attendance: Attendance Threshold Alerts
PR #40: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_alerts import AttendanceAlertsMaster, AttendanceAlertsAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_alerts")

@receiver(post_save, sender=AttendanceAlertsMaster)
def log_attendance_alerts_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendanceAlertsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendanceAlerts [{instance.id}] was {action}")
    AttendanceAlertsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendanceAlertsMaster)
def log_attendance_alerts_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendanceAlerts [{instance.id}] deletion requested.")
