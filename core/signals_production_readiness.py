"""
Django ORM Signal Listeners for Core: Production Readiness
PR #100: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models_production_readiness import ProductionReadinessMaster, ProductionReadinessAuditTransaction

logger = logging.getLogger("edutrack.core.signals.production_readiness")

@receiver(post_save, sender=ProductionReadinessMaster)
def log_production_readiness_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to ProductionReadinessAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: ProductionReadiness [{instance.id}] was {action}")
    ProductionReadinessAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=ProductionReadinessMaster)
def log_production_readiness_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: ProductionReadiness [{instance.id}] deletion requested.")
