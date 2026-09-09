"""
Django ORM Signal Listeners for Academics: Facilities & Classrooms
PR #14: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_classrooms import AcademicsClassroomsMaster, AcademicsClassroomsAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_classrooms")

@receiver(post_save, sender=AcademicsClassroomsMaster)
def log_academics_classrooms_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsClassroomsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsClassrooms [{instance.id}] was {action}")
    AcademicsClassroomsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsClassroomsMaster)
def log_academics_classrooms_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsClassrooms [{instance.id}] deletion requested.")
