"""
Django ORM Signal Listeners for Academics: Subject Architecture
PR #12: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_subjects import AcademicsSubjectsMaster, AcademicsSubjectsAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_subjects")

@receiver(post_save, sender=AcademicsSubjectsMaster)
def log_academics_subjects_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsSubjectsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsSubjects [{instance.id}] was {action}")
    AcademicsSubjectsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsSubjectsMaster)
def log_academics_subjects_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsSubjects [{instance.id}] deletion requested.")
