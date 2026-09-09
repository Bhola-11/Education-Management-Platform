"""
Django ORM Signal Listeners for Certificates: Certificate Issuance Pipeline
PR #73: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from certificates.models_certificates_issuance import CertificatesIssuanceMaster, CertificatesIssuanceAuditTransaction

logger = logging.getLogger("edutrack.certificates.signals.certificates_issuance")

@receiver(post_save, sender=CertificatesIssuanceMaster)
def log_certificates_issuance_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CertificatesIssuanceAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CertificatesIssuance [{instance.id}] was {action}")
    CertificatesIssuanceAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CertificatesIssuanceMaster)
def log_certificates_issuance_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CertificatesIssuance [{instance.id}] deletion requested.")
