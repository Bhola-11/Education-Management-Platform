"""
Django ORM Signal Listeners for Dashboards: Dean Academic Dashboard
PR #81: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from dashboards.models_dashboards_principal import DashboardsPrincipalMaster, DashboardsPrincipalAuditTransaction

logger = logging.getLogger("edutrack.dashboards.signals.dashboards_principal")

@receiver(post_save, sender=DashboardsPrincipalMaster)
def log_dashboards_principal_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to DashboardsPrincipalAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: DashboardsPrincipal [{instance.id}] was {action}")
    DashboardsPrincipalAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=DashboardsPrincipalMaster)
def log_dashboards_principal_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: DashboardsPrincipal [{instance.id}] deletion requested.")
