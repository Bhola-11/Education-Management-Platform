"""
Django ORM Signal Listeners for Timetables: Faculty Substitutions
PR #34: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from timetables.models_timetables_substitutions import TimetablesSubstitutionsMaster, TimetablesSubstitutionsAuditTransaction

logger = logging.getLogger("edutrack.timetables.signals.timetables_substitutions")

@receiver(post_save, sender=TimetablesSubstitutionsMaster)
def log_timetables_substitutions_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to TimetablesSubstitutionsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: TimetablesSubstitutions [{instance.id}] was {action}")
    TimetablesSubstitutionsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=TimetablesSubstitutionsMaster)
def log_timetables_substitutions_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: TimetablesSubstitutions [{instance.id}] deletion requested.")
