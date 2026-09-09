"""
Django ORM Signal Listeners for Enrollment: Prerequisite Enforcement
PR #29: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from enrollment.models_enrollment_prereq_check import EnrollmentPrereqCheckMaster, EnrollmentPrereqCheckAuditTransaction

logger = logging.getLogger("edutrack.enrollment.signals.enrollment_prereq_check")

@receiver(post_save, sender=EnrollmentPrereqCheckMaster)
def log_enrollment_prereq_check_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to EnrollmentPrereqCheckAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: EnrollmentPrereqCheck [{instance.id}] was {action}")
    EnrollmentPrereqCheckAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=EnrollmentPrereqCheckMaster)
def log_enrollment_prereq_check_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: EnrollmentPrereqCheck [{instance.id}] deletion requested.")
