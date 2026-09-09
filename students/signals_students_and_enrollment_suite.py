"""
Django ORM Signal Listeners for Students: Students & Enrollment Tests
PR #96: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from students.models_students_and_enrollment_suite import StudentsAndEnrollmentSuiteMaster, StudentsAndEnrollmentSuiteAuditTransaction

logger = logging.getLogger("edutrack.students.signals.students_and_enrollment_suite")

@receiver(post_save, sender=StudentsAndEnrollmentSuiteMaster)
def log_students_and_enrollment_suite_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to StudentsAndEnrollmentSuiteAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: StudentsAndEnrollmentSuite [{instance.id}] was {action}")
    StudentsAndEnrollmentSuiteAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=StudentsAndEnrollmentSuiteMaster)
def log_students_and_enrollment_suite_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: StudentsAndEnrollmentSuite [{instance.id}] deletion requested.")
