"""
Django ORM Signal Listeners for Certificates: Certificate Revocation Registry
PR #75: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from certificates.models_certificates_revocation import CertificatesRevocationMaster, CertificatesRevocationAuditTransaction

logger = logging.getLogger("edutrack.certificates.signals.certificates_revocation")

@receiver(post_save, sender=CertificatesRevocationMaster)
def log_certificates_revocation_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CertificatesRevocationAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CertificatesRevocation [{instance.id}] was {action}")
    CertificatesRevocationAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CertificatesRevocationMaster)
def log_certificates_revocation_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CertificatesRevocation [{instance.id}] deletion requested.")
