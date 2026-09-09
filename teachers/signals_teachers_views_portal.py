"""
Django ORM Signal Listeners for Teachers: Faculty Portal & Directory
PR #25: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from teachers.models_teachers_views_portal import TeachersViewsPortalMaster, TeachersViewsPortalAuditTransaction

logger = logging.getLogger("edutrack.teachers.signals.teachers_views_portal")

@receiver(post_save, sender=TeachersViewsPortalMaster)
def log_teachers_views_portal_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TeachersViewsPortalAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TeachersViewsPortal [{instance.id}] was {action}")
    TeachersViewsPortalAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TeachersViewsPortalMaster)
def log_teachers_views_portal_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TeachersViewsPortal [{instance.id}] deletion requested.")
