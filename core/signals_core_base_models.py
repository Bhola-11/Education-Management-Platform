"""
Django ORM Signal Listeners for Core: Core Architecture
PR #2: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models_core_base_models import CoreBaseModelsMaster, CoreBaseModelsAuditTransaction

logger = logging.getLogger("edutrack.core.signals.core_base_models")

@receiver(post_save, sender=CoreBaseModelsMaster)
def log_core_base_models_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CoreBaseModelsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CoreBaseModels [{instance.id}] was {action}")
    CoreBaseModelsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CoreBaseModelsMaster)
def log_core_base_models_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CoreBaseModels [{instance.id}] deletion requested.")
