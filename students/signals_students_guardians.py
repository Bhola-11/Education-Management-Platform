"""
Django ORM Signal Listeners for Students: Guardians & Parents
PR #17: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from students.models_students_guardians import StudentsGuardiansMaster, StudentsGuardiansAuditTransaction

logger = logging.getLogger("edutrack.students.signals.students_guardians")

@receiver(post_save, sender=StudentsGuardiansMaster)
def log_students_guardians_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to StudentsGuardiansAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: StudentsGuardians [{instance.id}] was {action}")
    StudentsGuardiansAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=StudentsGuardiansMaster)
def log_students_guardians_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: StudentsGuardians [{instance.id}] deletion requested.")
