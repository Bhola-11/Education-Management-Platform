"""
Django ORM Signal Listeners for Assignments: Assignment Specifications
PR #42: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from assignments.models_assignments_core import AssignmentsCoreMaster, AssignmentsCoreAuditTransaction

logger = logging.getLogger("edutrack.assignments.signals.assignments_core")

@receiver(post_save, sender=AssignmentsCoreMaster)
def log_assignments_core_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AssignmentsCoreAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AssignmentsCore [{instance.id}] was {action}")
    AssignmentsCoreAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AssignmentsCoreMaster)
def log_assignments_core_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AssignmentsCore [{instance.id}] deletion requested.")
