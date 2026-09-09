"""
Django ORM Signal Listeners for Fees: Fee Portals & Audit Views
PR #65: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_portal_views import FeesPortalViewsMaster, FeesPortalViewsAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_portal_views")

@receiver(post_save, sender=FeesPortalViewsMaster)
def log_fees_portal_views_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesPortalViewsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesPortalViews [{instance.id}] was {action}")
    FeesPortalViewsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesPortalViewsMaster)
def log_fees_portal_views_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesPortalViews [{instance.id}] deletion requested.")
