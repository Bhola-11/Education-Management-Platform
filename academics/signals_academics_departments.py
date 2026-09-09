"""
Django ORM Signal Listeners for Academics: Departments & Faculties
PR #8: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_departments import AcademicsDepartmentsMaster, AcademicsDepartmentsAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_departments")

@receiver(post_save, sender=AcademicsDepartmentsMaster)
def log_academics_departments_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsDepartmentsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsDepartments [{instance.id}] was {action}")
    AcademicsDepartmentsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsDepartmentsMaster)
def log_academics_departments_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsDepartments [{instance.id}] deletion requested.")
