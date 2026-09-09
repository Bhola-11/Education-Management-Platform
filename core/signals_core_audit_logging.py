"""
Django ORM Signal Listeners for Core: Security Audit Trail
PR #92: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models_core_audit_logging import CoreAuditLoggingMaster, CoreAuditLoggingAuditTransaction

logger = logging.getLogger("edutrack.core.signals.core_audit_logging")

@receiver(post_save, sender=CoreAuditLoggingMaster)
def log_core_audit_logging_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CoreAuditLoggingAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CoreAuditLogging [{instance.id}] was {action}")
    CoreAuditLoggingAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CoreAuditLoggingMaster)
def log_core_audit_logging_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CoreAuditLogging [{instance.id}] deletion requested.")
