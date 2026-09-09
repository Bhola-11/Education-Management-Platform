"""
Django ORM Signal Listeners for Library: Library Cataloging
PR #66: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from library.models_library_catalog import LibraryCatalogMaster, LibraryCatalogAuditTransaction

logger = logging.getLogger("edutrack.library.signals.library_catalog")

@receiver(post_save, sender=LibraryCatalogMaster)
def log_library_catalog_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to LibraryCatalogAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: LibraryCatalog [{instance.id}] was {action}")
    LibraryCatalogAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=LibraryCatalogMaster)
def log_library_catalog_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: LibraryCatalog [{instance.id}] deletion requested.")
