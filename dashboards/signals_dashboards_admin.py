"""
Django ORM Signal Listeners for Dashboards: Executive Dashboard
PR #80: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from dashboards.models_dashboards_admin import DashboardsAdminMaster, DashboardsAdminAuditTransaction

logger = logging.getLogger("edutrack.dashboards.signals.dashboards_admin")

@receiver(post_save, sender=DashboardsAdminMaster)
def log_dashboards_admin_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to DashboardsAdminAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: DashboardsAdmin [{instance.id}] was {action}")
    DashboardsAdminAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=DashboardsAdminMaster)
def log_dashboards_admin_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: DashboardsAdmin [{instance.id}] deletion requested.")
