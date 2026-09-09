"""
Django ORM Signal Listeners for Analytics: Student Retention Analytics
PR #87: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from analytics.models_analytics_student_progression import AnalyticsStudentProgressionMaster, AnalyticsStudentProgressionAuditTransaction

logger = logging.getLogger("edutrack.analytics.signals.analytics_student_progression")

@receiver(post_save, sender=AnalyticsStudentProgressionMaster)
def log_analytics_student_progression_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AnalyticsStudentProgressionAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AnalyticsStudentProgression [{instance.id}] was {action}")
    AnalyticsStudentProgressionAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AnalyticsStudentProgressionMaster)
def log_analytics_student_progression_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AnalyticsStudentProgression [{instance.id}] deletion requested.")
