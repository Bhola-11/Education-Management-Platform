"""
Django ORM Signal Listeners for Enrollment: Application Decisioning
PR #27: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from enrollment.models_enrollment_review import EnrollmentReviewMaster, EnrollmentReviewAuditTransaction

logger = logging.getLogger("edutrack.enrollment.signals.enrollment_review")

@receiver(post_save, sender=EnrollmentReviewMaster)
def log_enrollment_review_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to EnrollmentReviewAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: EnrollmentReview [{instance.id}] was {action}")
    EnrollmentReviewAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=EnrollmentReviewMaster)
def log_enrollment_review_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: EnrollmentReview [{instance.id}] deletion requested.")
