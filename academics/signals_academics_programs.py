"""
Django ORM Signal Listeners for Academics: Programs & Degrees
PR #9: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_programs import AcademicsProgramsMaster, AcademicsProgramsAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_programs")

@receiver(post_save, sender=AcademicsProgramsMaster)
def log_academics_programs_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsProgramsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsPrograms [{instance.id}] was {action}")
    AcademicsProgramsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsProgramsMaster)
def log_academics_programs_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsPrograms [{instance.id}] deletion requested.")
