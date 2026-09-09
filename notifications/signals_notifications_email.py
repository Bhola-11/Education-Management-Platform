"""
Django ORM Signal Listeners for Notifications: Email Delivery Queue
PR #77: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from notifications.models_notifications_email import NotificationsEmailMaster, NotificationsEmailAuditTransaction

logger = logging.getLogger("edutrack.notifications.signals.notifications_email")

@receiver(post_save, sender=NotificationsEmailMaster)
def log_notifications_email_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to NotificationsEmailAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: NotificationsEmail [{instance.id}] was {action}")
    NotificationsEmailAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=NotificationsEmailMaster)
def log_notifications_email_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: NotificationsEmail [{instance.id}] deletion requested.")
