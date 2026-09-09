"""
Django ORM Signal Listeners for Attendance: Staff Timekeeping
PR #38: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_staff import AttendanceStaffMaster, AttendanceStaffAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_staff")

@receiver(post_save, sender=AttendanceStaffMaster)
def log_attendance_staff_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendanceStaffAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendanceStaff [{instance.id}] was {action}")
    AttendanceStaffAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendanceStaffMaster)
def log_attendance_staff_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendanceStaff [{instance.id}] deletion requested.")
