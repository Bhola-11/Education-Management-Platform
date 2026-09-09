"""
Django ORM Signal Listeners for Exams: Admit Cards & Hall Tickets
PR #51: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from exams.models_exams_admit_cards import ExamsAdmitCardsMaster, ExamsAdmitCardsAuditTransaction

logger = logging.getLogger("edutrack.exams.signals.exams_admit_cards")

@receiver(post_save, sender=ExamsAdmitCardsMaster)
def log_exams_admit_cards_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to ExamsAdmitCardsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: ExamsAdmitCards [{instance.id}] was {action}")
    ExamsAdmitCardsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=ExamsAdmitCardsMaster)
def log_exams_admit_cards_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: ExamsAdmitCards [{instance.id}] deletion requested.")
