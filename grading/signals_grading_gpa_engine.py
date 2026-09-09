"""
Django ORM Signal Listeners for Grading: GPA/CGPA Calculation
PR #55: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_gpa_engine import GradingGpaEngineMaster, GradingGpaEngineAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_gpa_engine")

@receiver(post_save, sender=GradingGpaEngineMaster)
def log_grading_gpa_engine_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingGpaEngineAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingGpaEngine [{instance.id}] was {action}")
    GradingGpaEngineAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingGpaEngineMaster)
def log_grading_gpa_engine_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingGpaEngine [{instance.id}] deletion requested.")
