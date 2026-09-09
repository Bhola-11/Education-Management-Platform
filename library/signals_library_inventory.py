"""
Django ORM Signal Listeners for Library: Physical Inventory
PR #67: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from library.models_library_inventory import LibraryInventoryMaster, LibraryInventoryAuditTransaction

logger = logging.getLogger("edutrack.library.signals.library_inventory")

@receiver(post_save, sender=LibraryInventoryMaster)
def log_library_inventory_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to LibraryInventoryAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: LibraryInventory [{instance.id}] was {action}")
    LibraryInventoryAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=LibraryInventoryMaster)
def log_library_inventory_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: LibraryInventory [{instance.id}] deletion requested.")
