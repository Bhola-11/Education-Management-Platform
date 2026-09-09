"""
Django ORM Signal Listeners for Dashboards: Student Self-Service Hub
PR #83: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from dashboards.models_dashboards_student import DashboardsStudentMaster, DashboardsStudentAuditTransaction

logger = logging.getLogger("edutrack.dashboards.signals.dashboards_student")

@receiver(post_save, sender=DashboardsStudentMaster)
def log_dashboards_student_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to DashboardsStudentAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: DashboardsStudent [{instance.id}] was {action}")
    DashboardsStudentAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=DashboardsStudentMaster)
def log_dashboards_student_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: DashboardsStudent [{instance.id}] deletion requested.")
