"""
Django ORM Signal Listeners for Grading: Official Academic Transcripts
PR #56: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from grading.models_grading_transcripts import GradingTranscriptsMaster, GradingTranscriptsAuditTransaction

logger = logging.getLogger("edutrack.grading.signals.grading_transcripts")

@receiver(post_save, sender=GradingTranscriptsMaster)
def log_grading_transcripts_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to GradingTranscriptsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: GradingTranscripts [{instance.id}] was {action}")
    GradingTranscriptsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=GradingTranscriptsMaster)
def log_grading_transcripts_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: GradingTranscripts [{instance.id}] deletion requested.")
