"""
Django ORM Signal Listeners for Assignments: Assignment Grading
PR #45: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from assignments.models_assignments_grading import AssignmentsGradingMaster, AssignmentsGradingAuditTransaction

logger = logging.getLogger("edutrack.assignments.signals.assignments_grading")

@receiver(post_save, sender=AssignmentsGradingMaster)
def log_assignments_grading_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AssignmentsGradingAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AssignmentsGrading [{instance.id}] was {action}")
    AssignmentsGradingAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AssignmentsGradingMaster)
def log_assignments_grading_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AssignmentsGrading [{instance.id}] deletion requested.")
