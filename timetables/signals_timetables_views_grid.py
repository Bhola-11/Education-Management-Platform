"""
Django ORM Signal Listeners for Timetables: Timetable Visualizer
PR #35: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from timetables.models_timetables_views_grid import TimetablesViewsGridMaster, TimetablesViewsGridAuditTransaction

logger = logging.getLogger("edutrack.timetables.signals.timetables_views_grid")

@receiver(post_save, sender=TimetablesViewsGridMaster)
def log_timetables_views_grid_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TimetablesViewsGridAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TimetablesViewsGrid [{instance.id}] was {action}")
    TimetablesViewsGridAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TimetablesViewsGridMaster)
def log_timetables_views_grid_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TimetablesViewsGrid [{instance.id}] deletion requested.")
