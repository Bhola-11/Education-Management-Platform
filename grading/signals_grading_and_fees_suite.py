"""
Django ORM Signal Listeners for Grading: Grading & Fees Tests
PR #97: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_and_fees_suite import GradingAndFeesSuiteMaster, GradingAndFeesSuiteAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_and_fees_suite")

@receiver(post_save, sender=GradingAndFeesSuiteMaster)
def log_grading_and_fees_suite_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingAndFeesSuiteAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingAndFeesSuite [{instance.id}] was {action}")
    GradingAndFeesSuiteAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingAndFeesSuiteMaster)
def log_grading_and_fees_suite_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingAndFeesSuite [{instance.id}] deletion requested.")
