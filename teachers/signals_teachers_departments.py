"""
Django ORM Signal Listeners for Teachers: Department Affiliations
PR #23: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from teachers.models_teachers_departments import TeachersDepartmentsMaster, TeachersDepartmentsAuditTransaction

logger = logging.getLogger("edutrack.teachers.signals.teachers_departments")

@receiver(post_save, sender=TeachersDepartmentsMaster)
def log_teachers_departments_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TeachersDepartmentsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TeachersDepartments [{instance.id}] was {action}")
    TeachersDepartmentsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TeachersDepartmentsMaster)
def log_teachers_departments_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TeachersDepartments [{instance.id}] deletion requested.")
