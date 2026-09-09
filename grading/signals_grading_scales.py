"""
Django ORM Signal Listeners for Grading: Grade Scales & Rules
PR #52: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_scales import GradingScalesMaster, GradingScalesAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_scales")

@receiver(post_save, sender=GradingScalesMaster)
def log_grading_scales_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingScalesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingScales [{instance.id}] was {action}")
    GradingScalesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingScalesMaster)
def log_grading_scales_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingScales [{instance.id}] deletion requested.")
