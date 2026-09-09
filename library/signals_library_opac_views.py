"""
Django ORM Signal Listeners for Library: OPAC Public Catalog
PR #71: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from library.models_library_opac_views import LibraryOpacViewsMaster, LibraryOpacViewsAuditTransaction

logger = logging.getLogger("edutrack.library.signals.library_opac_views")

@receiver(post_save, sender=LibraryOpacViewsMaster)
def log_library_opac_views_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to LibraryOpacViewsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: LibraryOpacViews [{instance.id}] was {action}")
    LibraryOpacViewsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=LibraryOpacViewsMaster)
def log_library_opac_views_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: LibraryOpacViews [{instance.id}] deletion requested.")
