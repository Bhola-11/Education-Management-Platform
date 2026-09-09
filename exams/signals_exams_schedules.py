"""
Django ORM Signal Listeners for Exams: Exam Scheduling
PR #48: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from exams.models_exams_schedules import ExamsSchedulesMaster, ExamsSchedulesAuditTransaction

logger = logging.getLogger("edutrack.exams.signals.exams_schedules")

@receiver(post_save, sender=ExamsSchedulesMaster)
def log_exams_schedules_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to ExamsSchedulesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: ExamsSchedules [{instance.id}] was {action}")
    ExamsSchedulesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=ExamsSchedulesMaster)
def log_exams_schedules_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: ExamsSchedules [{instance.id}] deletion requested.")
