"""
Django ORM Signal Listeners for Fees: Fee Structures & Pricing
PR #58: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_structures import FeesStructuresMaster, FeesStructuresAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_structures")

@receiver(post_save, sender=FeesStructuresMaster)
def log_fees_structures_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesStructuresAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesStructures [{instance.id}] was {action}")
    FeesStructuresAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesStructuresMaster)
def log_fees_structures_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesStructures [{instance.id}] deletion requested.")
