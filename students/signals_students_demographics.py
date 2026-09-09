"""
Django ORM Signal Listeners for Students: Student Demographics
PR #16: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from students.models_students_demographics import StudentsDemographicsMaster, StudentsDemographicsAuditTransaction

logger = logging.getLogger("edutrack.students.signals.students_demographics")

@receiver(post_save, sender=StudentsDemographicsMaster)
def log_students_demographics_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to StudentsDemographicsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: StudentsDemographics [{instance.id}] was {action}")
    StudentsDemographicsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=StudentsDemographicsMaster)
def log_students_demographics_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: StudentsDemographics [{instance.id}] deletion requested.")
