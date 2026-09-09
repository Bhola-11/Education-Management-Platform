"""
Django ORM Signal Listeners for Core: Security & Penetration Tests
PR #99: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models_security_and_permissions_suite import SecurityAndPermissionsSuiteMaster, SecurityAndPermissionsSuiteAuditTransaction

logger = logging.getLogger("edutrack.core.signals.security_and_permissions_suite")

@receiver(post_save, sender=SecurityAndPermissionsSuiteMaster)
def log_security_and_permissions_suite_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to SecurityAndPermissionsSuiteAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: SecurityAndPermissionsSuite [{instance.id}] was {action}")
    SecurityAndPermissionsSuiteAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=SecurityAndPermissionsSuiteMaster)
def log_security_and_permissions_suite_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: SecurityAndPermissionsSuite [{instance.id}] deletion requested.")
