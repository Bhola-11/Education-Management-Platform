"""
Django ORM Signal Listeners for Fees: Installment Plans
PR #60: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_installments import FeesInstallmentsMaster, FeesInstallmentsAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_installments")

@receiver(post_save, sender=FeesInstallmentsMaster)
def log_fees_installments_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesInstallmentsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesInstallments [{instance.id}] was {action}")
    FeesInstallmentsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesInstallmentsMaster)
def log_fees_installments_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesInstallments [{instance.id}] deletion requested.")
