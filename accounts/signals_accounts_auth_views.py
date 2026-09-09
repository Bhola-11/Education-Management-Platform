"""
Django ORM Signal Listeners for Accounts: Authentication Views
PR #6: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from accounts.models_accounts_auth_views import AccountsAuthViewsMaster, AccountsAuthViewsAuditTransaction

logger = logging.getLogger("edutrack.accounts.signals.accounts_auth_views")

@receiver(post_save, sender=AccountsAuthViewsMaster)
def log_accounts_auth_views_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AccountsAuthViewsAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AccountsAuthViews [{instance.id}] was {action}")
    AccountsAuthViewsAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AccountsAuthViewsMaster)
def log_accounts_auth_views_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AccountsAuthViews [{instance.id}] deletion requested.")
