"""
Django ORM Signal Listeners for Notifications: Notification Center
PR #76: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from notifications.models_notifications_center import NotificationsCenterMaster, NotificationsCenterAuditTransaction

logger = logging.getLogger("edutrack.notifications.signals.notifications_center")

@receiver(post_save, sender=NotificationsCenterMaster)
def log_notifications_center_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to NotificationsCenterAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: NotificationsCenter [{instance.id}] was {action}")
    NotificationsCenterAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=NotificationsCenterMaster)
def log_notifications_center_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: NotificationsCenter [{instance.id}] deletion requested.")
