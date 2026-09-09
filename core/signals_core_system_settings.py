"""
Django ORM Signal Listeners for Core: Institutional Settings
PR #94: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models_core_system_settings import CoreSystemSettingsMaster, CoreSystemSettingsAuditTransaction

logger = logging.getLogger("edutrack.core.signals.core_system_settings")

@receiver(post_save, sender=CoreSystemSettingsMaster)
def log_core_system_settings_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CoreSystemSettingsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CoreSystemSettings [{instance.id}] was {action}")
    CoreSystemSettingsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CoreSystemSettingsMaster)
def log_core_system_settings_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CoreSystemSettings [{instance.id}] deletion requested.")
