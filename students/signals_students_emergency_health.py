"""
Django ORM Signal Listeners for Students: Student Health & Safety
PR #18: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from students.models_students_emergency_health import StudentsEmergencyHealthMaster, StudentsEmergencyHealthAuditTransaction

logger = logging.getLogger("edutrack.students.signals.students_emergency_health")

@receiver(post_save, sender=StudentsEmergencyHealthMaster)
def log_students_emergency_health_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to StudentsEmergencyHealthAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: StudentsEmergencyHealth [{instance.id}] was {action}")
    StudentsEmergencyHealthAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=StudentsEmergencyHealthMaster)
def log_students_emergency_health_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: StudentsEmergencyHealth [{instance.id}] deletion requested.")
