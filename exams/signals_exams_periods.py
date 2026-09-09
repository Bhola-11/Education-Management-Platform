"""
Django ORM Signal Listeners for Exams: Exam Cycles & Series
PR #47: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from exams.models_exams_periods import ExamsPeriodsMaster, ExamsPeriodsAuditTransaction

logger = logging.getLogger("edutrack.exams.signals.exams_periods")

@receiver(post_save, sender=ExamsPeriodsMaster)
def log_exams_periods_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to ExamsPeriodsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: ExamsPeriods [{instance.id}] was {action}")
    ExamsPeriodsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=ExamsPeriodsMaster)
def log_exams_periods_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: ExamsPeriods [{instance.id}] deletion requested.")
