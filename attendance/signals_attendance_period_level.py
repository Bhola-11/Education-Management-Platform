"""
Django ORM Signal Listeners for Attendance: Period Attendance
PR #37: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_period_level import AttendancePeriodLevelMaster, AttendancePeriodLevelAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_period_level")

@receiver(post_save, sender=AttendancePeriodLevelMaster)
def log_attendance_period_level_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendancePeriodLevelAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendancePeriodLevel [{instance.id}] was {action}")
    AttendancePeriodLevelAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendancePeriodLevelMaster)
def log_attendance_period_level_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendancePeriodLevel [{instance.id}] deletion requested.")
