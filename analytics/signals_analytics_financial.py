"""
Django ORM Signal Listeners for Analytics: Institutional Financial Analytics
PR #88: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from analytics.models_analytics_financial import AnalyticsFinancialMaster, AnalyticsFinancialAuditTransaction

logger = logging.getLogger("edutrack.analytics.signals.analytics_financial")

@receiver(post_save, sender=AnalyticsFinancialMaster)
def log_analytics_financial_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AnalyticsFinancialAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AnalyticsFinancial [{instance.id}] was {action}")
    AnalyticsFinancialAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AnalyticsFinancialMaster)
def log_analytics_financial_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AnalyticsFinancial [{instance.id}] deletion requested.")
