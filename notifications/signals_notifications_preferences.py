"""
Django ORM Signal Listeners for Notifications: Notification Preferences
PR #79: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from notifications.models_notifications_preferences import NotificationsPreferencesMaster, NotificationsPreferencesAuditTransaction

logger = logging.getLogger("edutrack.notifications.signals.notifications_preferences")

@receiver(post_save, sender=NotificationsPreferencesMaster)
def log_notifications_preferences_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to NotificationsPreferencesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: NotificationsPreferences [{instance.id}] was {action}")
    NotificationsPreferencesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=NotificationsPreferencesMaster)
def log_notifications_preferences_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: NotificationsPreferences [{instance.id}] deletion requested.")
