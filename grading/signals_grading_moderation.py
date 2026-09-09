"""
Django ORM Signal Listeners for Grading: Marks Moderation Workflow
PR #54: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_moderation import GradingModerationMaster, GradingModerationAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_moderation")

@receiver(post_save, sender=GradingModerationMaster)
def log_grading_moderation_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingModerationAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingModeration [{instance.id}] was {action}")
    GradingModerationAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingModerationMaster)
def log_grading_moderation_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingModeration [{instance.id}] deletion requested.")
