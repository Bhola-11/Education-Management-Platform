"""
Django ORM Signal Listeners for Timetables: Schedule Conflict Solver
PR #33: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from timetables.models_timetables_conflict_detector import TimetablesConflictDetectorMaster, TimetablesConflictDetectorAuditTransaction

logger = logging.getLogger("edutrack.timetables.signals.timetables_conflict_detector")

@receiver(post_save, sender=TimetablesConflictDetectorMaster)
def log_timetables_conflict_detector_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TimetablesConflictDetectorAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TimetablesConflictDetector [{instance.id}] was {action}")
    TimetablesConflictDetectorAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TimetablesConflictDetectorMaster)
def log_timetables_conflict_detector_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TimetablesConflictDetector [{instance.id}] deletion requested.")
