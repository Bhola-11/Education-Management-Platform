"""
Django ORM Signal Listeners for Students: Student Lifecycle
PR #19: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from students.models_students_lifecycle import StudentsLifecycleMaster, StudentsLifecycleAuditTransaction

logger = logging.getLogger("edutrack.students.signals.students_lifecycle")

@receiver(post_save, sender=StudentsLifecycleMaster)
def log_students_lifecycle_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to StudentsLifecycleAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: StudentsLifecycle [{instance.id}] was {action}")
    StudentsLifecycleAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=StudentsLifecycleMaster)
def log_students_lifecycle_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: StudentsLifecycle [{instance.id}] deletion requested.")
