"""
Django ORM Signal Listeners for Assignments: Academic Integrity
PR #46: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from assignments.models_assignments_plagiarism import AssignmentsPlagiarismMaster, AssignmentsPlagiarismAuditTransaction

logger = logging.getLogger("edutrack.assignments.signals.assignments_plagiarism")

@receiver(post_save, sender=AssignmentsPlagiarismMaster)
def log_assignments_plagiarism_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AssignmentsPlagiarismAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AssignmentsPlagiarism [{instance.id}] was {action}")
    AssignmentsPlagiarismAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AssignmentsPlagiarismMaster)
def log_assignments_plagiarism_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AssignmentsPlagiarism [{instance.id}] deletion requested.")
