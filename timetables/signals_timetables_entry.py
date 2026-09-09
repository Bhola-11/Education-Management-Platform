"""
Django ORM Signal Listeners for Timetables: Timetable Matrix
PR #32: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from timetables.models_timetables_entry import TimetablesEntryMaster, TimetablesEntryAuditTransaction

logger = logging.getLogger("edutrack.timetables.signals.timetables_entry")

@receiver(post_save, sender=TimetablesEntryMaster)
def log_timetables_entry_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TimetablesEntryAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TimetablesEntry [{instance.id}] was {action}")
    TimetablesEntryAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TimetablesEntryMaster)
def log_timetables_entry_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TimetablesEntry [{instance.id}] deletion requested.")
