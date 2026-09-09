"""
Django ORM Signal Listeners for Dashboards: Faculty Workplace Hub
PR #82: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from dashboards.models_dashboards_teacher import DashboardsTeacherMaster, DashboardsTeacherAuditTransaction

logger = logging.getLogger("edutrack.dashboards.signals.dashboards_teacher")

@receiver(post_save, sender=DashboardsTeacherMaster)
def log_dashboards_teacher_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to DashboardsTeacherAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: DashboardsTeacher [{instance.id}] was {action}")
    DashboardsTeacherAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=DashboardsTeacherMaster)
def log_dashboards_teacher_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: DashboardsTeacher [{instance.id}] deletion requested.")
