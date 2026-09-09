"""
Django ORM Signal Listeners for Teachers: Faculty Master Record
PR #21: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from teachers.models_teachers_master_record import TeachersMasterRecordMaster, TeachersMasterRecordAuditTransaction

logger = logging.getLogger("edutrack.teachers.signals.teachers_master_record")

@receiver(post_save, sender=TeachersMasterRecordMaster)
def log_teachers_master_record_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TeachersMasterRecordAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TeachersMasterRecord [{instance.id}] was {action}")
    TeachersMasterRecordAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TeachersMasterRecordMaster)
def log_teachers_master_record_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TeachersMasterRecord [{instance.id}] deletion requested.")
