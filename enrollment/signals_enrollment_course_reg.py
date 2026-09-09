"""
Django ORM Signal Listeners for Enrollment: Course Registration
PR #28: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from enrollment.models_enrollment_course_reg import EnrollmentCourseRegMaster, EnrollmentCourseRegAuditTransaction

logger = logging.getLogger("edutrack.enrollment.signals.enrollment_course_reg")

@receiver(post_save, sender=EnrollmentCourseRegMaster)
def log_enrollment_course_reg_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to EnrollmentCourseRegAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: EnrollmentCourseReg [{instance.id}] was {action}")
    EnrollmentCourseRegAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=EnrollmentCourseRegMaster)
def log_enrollment_course_reg_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: EnrollmentCourseReg [{instance.id}] deletion requested.")
