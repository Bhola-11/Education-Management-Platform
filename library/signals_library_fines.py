"""
Django ORM Signal Listeners for Library: Library Overdue Fines
PR #70: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from library.models_library_fines import LibraryFinesMaster, LibraryFinesAuditTransaction

logger = logging.getLogger("edutrack.library.signals.library_fines")

@receiver(post_save, sender=LibraryFinesMaster)
def log_library_fines_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to LibraryFinesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: LibraryFines [{instance.id}] was {action}")
    LibraryFinesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=LibraryFinesMaster)
def log_library_fines_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: LibraryFines [{instance.id}] deletion requested.")
