"""
Django ORM Signal Listeners for Attendance: Leave Workflow
PR #39: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from attendance.models_attendance_leave_workflow import AttendanceLeaveWorkflowMaster, AttendanceLeaveWorkflowAuditTransaction

logger = logging.getLogger("edutrack.attendance.signals.attendance_leave_workflow")

@receiver(post_save, sender=AttendanceLeaveWorkflowMaster)
def log_attendance_leave_workflow_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AttendanceLeaveWorkflowAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AttendanceLeaveWorkflow [{instance.id}] was {action}")
    AttendanceLeaveWorkflowAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AttendanceLeaveWorkflowMaster)
def log_attendance_leave_workflow_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AttendanceLeaveWorkflow [{instance.id}] deletion requested.")
