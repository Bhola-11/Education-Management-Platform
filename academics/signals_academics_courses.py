"""
Django ORM Signal Listeners for Academics: Course Catalog
PR #11: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_courses import AcademicsCoursesMaster, AcademicsCoursesAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_courses")

@receiver(post_save, sender=AcademicsCoursesMaster)
def log_academics_courses_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsCoursesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsCourses [{instance.id}] was {action}")
    AcademicsCoursesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsCoursesMaster)
def log_academics_courses_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsCourses [{instance.id}] deletion requested.")
