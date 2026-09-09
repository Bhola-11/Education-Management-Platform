"""
Django ORM Signal Listeners for Exams: Exam Seating Matrix
PR #49: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from exams.models_exams_hall_seating import ExamsHallSeatingMaster, ExamsHallSeatingAuditTransaction

logger = logging.getLogger("edutrack.exams.signals.exams_hall_seating")

@receiver(post_save, sender=ExamsHallSeatingMaster)
def log_exams_hall_seating_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to ExamsHallSeatingAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: ExamsHallSeating [{instance.id}] was {action}")
    ExamsHallSeatingAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=ExamsHallSeatingMaster)
def log_exams_hall_seating_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: ExamsHallSeating [{instance.id}] deletion requested.")
