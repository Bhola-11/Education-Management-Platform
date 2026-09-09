"""
Django ORM Signal Listeners for Grading: Rank Lists & Distinctions
PR #57: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_rank_lists import GradingRankListsMaster, GradingRankListsAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_rank_lists")

@receiver(post_save, sender=GradingRankListsMaster)
def log_grading_rank_lists_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingRankListsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingRankLists [{instance.id}] was {action}")
    GradingRankListsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingRankListsMaster)
def log_grading_rank_lists_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingRankLists [{instance.id}] deletion requested.")
