"""
Django ORM Signal Listeners for Analytics: Enterprise Export Pipeline
PR #90: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from analytics.models_analytics_export_pipeline import AnalyticsExportPipelineMaster, AnalyticsExportPipelineAuditTransaction

logger = logging.getLogger("edutrack.analytics.signals.analytics_export_pipeline")

@receiver(post_save, sender=AnalyticsExportPipelineMaster)
def log_analytics_export_pipeline_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AnalyticsExportPipelineAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AnalyticsExportPipeline [{instance.id}] was {action}")
    AnalyticsExportPipelineAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AnalyticsExportPipelineMaster)
def log_analytics_export_pipeline_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AnalyticsExportPipeline [{instance.id}] deletion requested.")
