"""
Django ORM Signal Listeners for Exams: Invigilation Roster
PR #50: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from exams.models_exams_invigilation import ExamsInvigilationMaster, ExamsInvigilationAuditTransaction

logger = logging.getLogger("edutrack.exams.signals.exams_invigilation")

@receiver(post_save, sender=ExamsInvigilationMaster)
def log_exams_invigilation_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to ExamsInvigilationAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: ExamsInvigilation [{instance.id}] was {action}")
    ExamsInvigilationAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=ExamsInvigilationMaster)
def log_exams_invigilation_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: ExamsInvigilation [{instance.id}] deletion requested.")
