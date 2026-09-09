"""
Django ORM Signal Listeners for Fees: Scholarships & Waivers
PR #61: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from fees.models_fees_scholarships import FeesScholarshipsMaster, FeesScholarshipsAuditTransaction

logger = logging.getLogger("edutrack.fees.signals.fees_scholarships")

@receiver(post_save, sender=FeesScholarshipsMaster)
def log_fees_scholarships_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to FeesScholarshipsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: FeesScholarships [{instance.id}] was {action}")
    FeesScholarshipsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=FeesScholarshipsMaster)
def log_fees_scholarships_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: FeesScholarships [{instance.id}] deletion requested.")
