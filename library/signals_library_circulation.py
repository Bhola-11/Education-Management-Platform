"""
Django ORM Signal Listeners for Library: Book Circulation Desk
PR #68: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from library.models_library_circulation import LibraryCirculationMaster, LibraryCirculationAuditTransaction

logger = logging.getLogger("edutrack.library.signals.library_circulation")

@receiver(post_save, sender=LibraryCirculationMaster)
def log_library_circulation_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to LibraryCirculationAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: LibraryCirculation [{instance.id}] was {action}")
    LibraryCirculationAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=LibraryCirculationMaster)
def log_library_circulation_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: LibraryCirculation [{instance.id}] deletion requested.")
