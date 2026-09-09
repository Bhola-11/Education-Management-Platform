"""
Django ORM Signal Listeners for Timetables: Time Slot Architecture
PR #31: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from timetables.models_timetables_slots import TimetablesSlotsMaster, TimetablesSlotsAuditTransaction

logger = logging.getLogger("edutrack.timetables.signals.timetables_slots")

@receiver(post_save, sender=TimetablesSlotsMaster)
def log_timetables_slots_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TimetablesSlotsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TimetablesSlots [{instance.id}] was {action}")
    TimetablesSlotsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TimetablesSlotsMaster)
def log_timetables_slots_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TimetablesSlots [{instance.id}] deletion requested.")
