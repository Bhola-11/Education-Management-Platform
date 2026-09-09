"""
Django ORM Signal Listeners for Students: Student Portal & Directory
PR #20: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from students.models_students_views_portal import StudentsViewsPortalMaster, StudentsViewsPortalAuditTransaction

logger = logging.getLogger("edutrack.students.signals.students_views_portal")

@receiver(post_save, sender=StudentsViewsPortalMaster)
def log_students_views_portal_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to StudentsViewsPortalAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: StudentsViewsPortal [{instance.id}] was {action}")
    StudentsViewsPortalAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=StudentsViewsPortalMaster)
def log_students_views_portal_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: StudentsViewsPortal [{instance.id}] deletion requested.")
