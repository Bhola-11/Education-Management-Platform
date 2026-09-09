"""
Django ORM Signal Listeners for Library: Reservations & Holds
PR #69: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from library.models_library_reservations import LibraryReservationsMaster, LibraryReservationsAuditTransaction

logger = logging.getLogger("edutrack.library.signals.library_reservations")

@receiver(post_save, sender=LibraryReservationsMaster)
def log_library_reservations_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to LibraryReservationsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: LibraryReservations [{instance.id}] was {action}")
    LibraryReservationsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=LibraryReservationsMaster)
def log_library_reservations_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: LibraryReservations [{instance.id}] deletion requested.")
