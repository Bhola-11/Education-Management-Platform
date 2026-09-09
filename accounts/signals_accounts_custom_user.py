"""
Django ORM Signal Listeners for Accounts: Authentication
PR #3: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from accounts.models_accounts_custom_user import AccountsCustomUserMaster, AccountsCustomUserAuditTransaction

logger = logging.getLogger("edutrack.accounts.signals.accounts_custom_user")

@receiver(post_save, sender=AccountsCustomUserMaster)
def log_accounts_custom_user_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AccountsCustomUserAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AccountsCustomUser [{instance.id}] was {action}")
    AccountsCustomUserAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AccountsCustomUserMaster)
def log_accounts_custom_user_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AccountsCustomUser [{instance.id}] deletion requested.")
