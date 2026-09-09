"""
Django ORM Signal Listeners for Fees: Student Fee Invoicing
PR #59: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_invoicing import FeesInvoicingMaster, FeesInvoicingAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_invoicing")

@receiver(post_save, sender=FeesInvoicingMaster)
def log_fees_invoicing_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesInvoicingAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesInvoicing [{instance.id}] was {action}")
    FeesInvoicingAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesInvoicingMaster)
def log_fees_invoicing_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesInvoicing [{instance.id}] deletion requested.")
