"""
Django ORM Signal Listeners for Dashboards: Librarian Ops Hub
PR #86: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from dashboards.models_dashboards_librarian import DashboardsLibrarianMaster, DashboardsLibrarianAuditTransaction

logger = logging.getLogger("edutrack.dashboards.signals.dashboards_librarian")

@receiver(post_save, sender=DashboardsLibrarianMaster)
def log_dashboards_librarian_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to DashboardsLibrarianAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: DashboardsLibrarian [{instance.id}] was {action}")
    DashboardsLibrarianAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=DashboardsLibrarianMaster)
def log_dashboards_librarian_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: DashboardsLibrarian [{instance.id}] deletion requested.")
