"""
Django ORM Signal Listeners for Fees: Payment Processing
PR #62: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_payments import FeesPaymentsMaster, FeesPaymentsAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_payments")

@receiver(post_save, sender=FeesPaymentsMaster)
def log_fees_payments_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesPaymentsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesPayments [{instance.id}] was {action}")
    FeesPaymentsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesPaymentsMaster)
def log_fees_payments_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesPayments [{instance.id}] deletion requested.")
