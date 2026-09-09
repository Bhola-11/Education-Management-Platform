"""
Django ORM Signal Listeners for Fees: Late Fee Penalties
PR #64: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_penalties import FeesPenaltiesMaster, FeesPenaltiesAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_penalties")

@receiver(post_save, sender=FeesPenaltiesMaster)
def log_fees_penalties_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesPenaltiesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesPenalties [{instance.id}] was {action}")
    FeesPenaltiesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesPenaltiesMaster)
def log_fees_penalties_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesPenalties [{instance.id}] deletion requested.")
