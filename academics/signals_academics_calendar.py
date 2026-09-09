"""
Django ORM Signal Listeners for Academics: Academic Calendar
PR #10: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from academics.models_academics_calendar import AcademicsCalendarMaster, AcademicsCalendarAuditTransaction

logger = logging.getLogger("edutrack.academics.signals.academics_calendar")

@receiver(post_save, sender=AcademicsCalendarMaster)
def log_academics_calendar_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AcademicsCalendarAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AcademicsCalendar [{instance.id}] was {action}")
    AcademicsCalendarAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AcademicsCalendarMaster)
def log_academics_calendar_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AcademicsCalendar [{instance.id}] deletion requested.")
