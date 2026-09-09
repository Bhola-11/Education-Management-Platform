"""
Django ORM Signal Listeners for Enrollment: Admissions Pipeline
PR #26: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from enrollment.models_enrollment_admissions import EnrollmentAdmissionsMaster, EnrollmentAdmissionsAuditTransaction

logger = logging.getLogger("edutrack.enrollment.signals.enrollment_admissions")

@receiver(post_save, sender=EnrollmentAdmissionsMaster)
def log_enrollment_admissions_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to EnrollmentAdmissionsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: EnrollmentAdmissions [{instance.id}] was {action}")
    EnrollmentAdmissionsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=EnrollmentAdmissionsMaster)
def log_enrollment_admissions_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: EnrollmentAdmissions [{instance.id}] deletion requested.")
