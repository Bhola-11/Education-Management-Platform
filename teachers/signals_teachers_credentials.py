"""
Django ORM Signal Listeners for Teachers: Faculty Credentials
PR #22: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from teachers.models_teachers_credentials import TeachersCredentialsMaster, TeachersCredentialsAuditTransaction

logger = logging.getLogger("edutrack.teachers.signals.teachers_credentials")

@receiver(post_save, sender=TeachersCredentialsMaster)
def log_teachers_credentials_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TeachersCredentialsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TeachersCredentials [{instance.id}] was {action}")
    TeachersCredentialsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TeachersCredentialsMaster)
def log_teachers_credentials_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TeachersCredentials [{instance.id}] deletion requested.")
