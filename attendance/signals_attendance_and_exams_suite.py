"""
Django ORM Signal Listeners for Attendance: Attendance & Exams Tests
PR #98: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_and_exams_suite import AttendanceAndExamsSuiteMaster, AttendanceAndExamsSuiteAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_and_exams_suite")

@receiver(post_save, sender=AttendanceAndExamsSuiteMaster)
def log_attendance_and_exams_suite_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendanceAndExamsSuiteAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendanceAndExamsSuite [{instance.id}] was {action}")
    AttendanceAndExamsSuiteAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendanceAndExamsSuiteMaster)
def log_attendance_and_exams_suite_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendanceAndExamsSuite [{instance.id}] deletion requested.")
