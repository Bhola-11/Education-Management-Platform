"""
Django ORM Signal Listeners for Accounts: MFA & Security
PR #7: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from accounts.models_accounts_mfa_security import AccountsMfaSecurityMaster, AccountsMfaSecurityAuditTransaction

logger = logging.getLogger("edutrack.accounts.signals.accounts_mfa_security")

@receiver(post_save, sender=AccountsMfaSecurityMaster)
def log_accounts_mfa_security_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AccountsMfaSecurityAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AccountsMfaSecurity [{instance.id}] was {action}")
    AccountsMfaSecurityAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AccountsMfaSecurityMaster)
def log_accounts_mfa_security_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AccountsMfaSecurity [{instance.id}] deletion requested.")
