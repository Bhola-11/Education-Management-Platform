"""
Django ORM Signal Listeners for Fees: Fee Ledger & Accounting
PR #63: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_reconciliation import FeesReconciliationMaster, FeesReconciliationAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_reconciliation")

@receiver(post_save, sender=FeesReconciliationMaster)
def log_fees_reconciliation_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesReconciliationAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesReconciliation [{instance.id}] was {action}")
    FeesReconciliationAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesReconciliationMaster)
def log_fees_reconciliation_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesReconciliation [{instance.id}] deletion requested.")
