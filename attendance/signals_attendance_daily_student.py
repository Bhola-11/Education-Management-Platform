"""
Django ORM Signal Listeners for Attendance: Daily Student Attendance
PR #36: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_daily_student import AttendanceDailyStudentMaster, AttendanceDailyStudentAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_daily_student")

@receiver(post_save, sender=AttendanceDailyStudentMaster)
def log_attendance_daily_student_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendanceDailyStudentAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendanceDailyStudent [{instance.id}] was {action}")
    AttendanceDailyStudentAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendanceDailyStudentMaster)
def log_attendance_daily_student_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendanceDailyStudent [{instance.id}] deletion requested.")
