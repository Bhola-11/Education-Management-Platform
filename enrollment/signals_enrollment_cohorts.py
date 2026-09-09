"""
Django ORM Signal Listeners for Enrollment: Cohorts & Sections
PR #30: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from enrollment.models_enrollment_cohorts import EnrollmentCohortsMaster, EnrollmentCohortsAuditTransaction

logger = logging.getLogger("edutrack.enrollment.signals.enrollment_cohorts")

@receiver(post_save, sender=EnrollmentCohortsMaster)
def log_enrollment_cohorts_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to EnrollmentCohortsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: EnrollmentCohorts [{instance.id}] was {action}")
    EnrollmentCohortsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=EnrollmentCohortsMaster)
def log_enrollment_cohorts_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: EnrollmentCohorts [{instance.id}] deletion requested.")
