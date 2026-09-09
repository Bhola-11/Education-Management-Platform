"""
Django ORM Signal Listeners for Core: Database Diagnostics & Snapshots
PR #93: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models_core_backup_restore import CoreBackupRestoreMaster, CoreBackupRestoreAuditTransaction

logger = logging.getLogger("edutrack.core.signals.core_backup_restore")

@receiver(post_save, sender=CoreBackupRestoreMaster)
def log_core_backup_restore_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CoreBackupRestoreAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CoreBackupRestore [{instance.id}] was {action}")
    CoreBackupRestoreAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CoreBackupRestoreMaster)
def log_core_backup_restore_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CoreBackupRestore [{instance.id}] deletion requested.")
