"""
Django ORM Signal Listeners for Assignments: Evaluation Rubrics
PR #44: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from assignments.models_assignments_rubrics import AssignmentsRubricsMaster, AssignmentsRubricsAuditTransaction

logger = logging.getLogger("edutrack.assignments.signals.assignments_rubrics")

@receiver(post_save, sender=AssignmentsRubricsMaster)
def log_assignments_rubrics_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AssignmentsRubricsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AssignmentsRubrics [{instance.id}] was {action}")
    AssignmentsRubricsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AssignmentsRubricsMaster)
def log_assignments_rubrics_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AssignmentsRubrics [{instance.id}] deletion requested.")
