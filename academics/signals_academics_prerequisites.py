"""
Django ORM Signal Listeners for Academics: Prerequisites & Rules
PR #13: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_prerequisites import AcademicsPrerequisitesMaster, AcademicsPrerequisitesAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_prerequisites")

@receiver(post_save, sender=AcademicsPrerequisitesMaster)
def log_academics_prerequisites_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsPrerequisitesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsPrerequisites [{instance.id}] was {action}")
    AcademicsPrerequisitesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsPrerequisitesMaster)
def log_academics_prerequisites_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsPrerequisites [{instance.id}] deletion requested.")
