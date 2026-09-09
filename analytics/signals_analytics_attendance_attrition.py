"""
Django ORM Signal Listeners for Analytics: Attendance Attrition Models
PR #89: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from analytics.models_analytics_attendance_attrition import AnalyticsAttendanceAttritionMaster, AnalyticsAttendanceAttritionAuditTransaction

logger = logging.getLogger("edutrack.analytics.signals.analytics_attendance_attrition")

@receiver(post_save, sender=AnalyticsAttendanceAttritionMaster)
def log_analytics_attendance_attrition_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AnalyticsAttendanceAttritionAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AnalyticsAttendanceAttrition [{instance.id}] was {action}")
    AnalyticsAttendanceAttritionAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AnalyticsAttendanceAttritionMaster)
def log_analytics_attendance_attrition_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AnalyticsAttendanceAttrition [{instance.id}] deletion requested.")
