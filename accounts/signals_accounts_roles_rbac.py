"""
Django ORM Signal Listeners for Accounts: Role-Based Access Control
PR #4: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from accounts.models_accounts_roles_rbac import AccountsRolesRbacMaster, AccountsRolesRbacAuditTransaction

logger = logging.getLogger("edutrack.accounts.signals.accounts_roles_rbac")

@receiver(post_save, sender=AccountsRolesRbacMaster)
def log_accounts_roles_rbac_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AccountsRolesRbacAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AccountsRolesRbac [{instance.id}] was {action}")
    AccountsRolesRbacAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AccountsRolesRbacMaster)
def log_accounts_roles_rbac_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AccountsRolesRbac [{instance.id}] deletion requested.")
