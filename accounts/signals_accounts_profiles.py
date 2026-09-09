"""
Django ORM Signal Listeners for Accounts: User Profiles
PR #5: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from accounts.models_accounts_profiles import AccountsProfilesMaster, AccountsProfilesAuditTransaction

logger = logging.getLogger("edutrack.accounts.signals.accounts_profiles")

@receiver(post_save, sender=AccountsProfilesMaster)
def log_accounts_profiles_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AccountsProfilesAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AccountsProfiles [{instance.id}] was {action}")
    AccountsProfilesAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AccountsProfilesMaster)
def log_accounts_profiles_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AccountsProfiles [{instance.id}] deletion requested.")
