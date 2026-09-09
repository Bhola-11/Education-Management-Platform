"""
Django ORM Signal Listeners for Certificates: Cryptographic Verification
PR #74: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from certificates.models_certificates_verification import CertificatesVerificationMaster, CertificatesVerificationAuditTransaction

logger = logging.getLogger("edutrack.certificates.signals.certificates_verification")

@receiver(post_save, sender=CertificatesVerificationMaster)
def log_certificates_verification_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to CertificatesVerificationAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: CertificatesVerification [{instance.id}] was {action}")
    CertificatesVerificationAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=CertificatesVerificationMaster)
def log_certificates_verification_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: CertificatesVerification [{instance.id}] deletion requested.")
