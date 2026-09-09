"""
Django ORM Signal Listeners for Certificates: Certificate Template Designer
PR #72: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from certificates.models_certificates_templates import CertificatesTemplatesMaster, CertificatesTemplatesAuditTransaction

logger = logging.getLogger("edutrack.certificates.signals.certificates_templates")

@receiver(post_save, sender=CertificatesTemplatesMaster)
def log_certificates_templates_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CertificatesTemplatesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CertificatesTemplates [{instance.id}] was {action}")
    CertificatesTemplatesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CertificatesTemplatesMaster)
def log_certificates_templates_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CertificatesTemplates [{instance.id}] deletion requested.")
