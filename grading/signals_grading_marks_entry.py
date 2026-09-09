"""
Django ORM Signal Listeners for Grading: Marks Evaluation Sheet
PR #53: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_marks_entry import GradingMarksEntryMaster, GradingMarksEntryAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_marks_entry")

@receiver(post_save, sender=GradingMarksEntryMaster)
def log_grading_marks_entry_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingMarksEntryAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingMarksEntry [{instance.id}] was {action}")
    GradingMarksEntryAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingMarksEntryMaster)
def log_grading_marks_entry_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingMarksEntry [{instance.id}] deletion requested.")
