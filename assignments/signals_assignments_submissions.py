"""
Django ORM Signal Listeners for Assignments: Student Submissions
PR #43: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from assignments.models_assignments_submissions import AssignmentsSubmissionsMaster, AssignmentsSubmissionsAuditTransaction

logger = logging.getLogger("edutrack.assignments.signals.assignments_submissions")

@receiver(post_save, sender=AssignmentsSubmissionsMaster)
def log_assignments_submissions_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AssignmentsSubmissionsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AssignmentsSubmissions [{instance.id}] was {action}")
    AssignmentsSubmissionsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AssignmentsSubmissionsMaster)
def log_assignments_submissions_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AssignmentsSubmissions [{instance.id}] deletion requested.")
