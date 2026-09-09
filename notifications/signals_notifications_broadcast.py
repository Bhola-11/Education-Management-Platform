"""
Django ORM Signal Listeners for Notifications: Campus Broadcasts
PR #78: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from notifications.models_notifications_broadcast import NotificationsBroadcastMaster, NotificationsBroadcastAuditTransaction

logger = logging.getLogger("edutrack.notifications.signals.notifications_broadcast")

@receiver(post_save, sender=NotificationsBroadcastMaster)
def log_notifications_broadcast_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to NotificationsBroadcastAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: NotificationsBroadcast [{instance.id}] was {action}")
    NotificationsBroadcastAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=NotificationsBroadcastMaster)
def log_notifications_broadcast_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: NotificationsBroadcast [{instance.id}] deletion requested.")
