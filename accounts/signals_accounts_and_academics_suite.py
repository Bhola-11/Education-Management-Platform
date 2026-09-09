"""
Django ORM Signal Listeners for Accounts: Accounts & Academics Tests
PR #95: Audit Trigger Hooks and Telemetry Logging.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from accounts.models_accounts_and_academics_suite import AccountsAndAcademicsSuiteMaster, AccountsAndAcademicsSuiteAuditTransaction

logger = logging.getLogger("edutrack.accounts.signals.accounts_and_academics_suite")

@receiver(post_save, sender=AccountsAndAcademicsSuiteMaster)
def log_accounts_and_academics_suite_save_mutation(sender, instance, created, **kwargs):
    """Logs lifecycle changes to AccountsAndAcademicsSuiteAuditTransaction."""
    action = "CREATED" if created else "UPDATED"
    logger.info(f"Signal caught: AccountsAndAcademicsSuite [{instance.id}] was {action}")
    AccountsAndAcademicsSuiteAuditTransaction.objects.create(
        code=f"SIG-{instance.code}-{action}",
        name=f"Entity {action}: {instance.name}",
        description=f"Auto-generated audit log via Django ORM post_save signal.",
        status="RECORDED"
    )

@receiver(pre_delete, sender=AccountsAndAcademicsSuiteMaster)
def log_accounts_and_academics_suite_deletion(sender, instance, **kwargs):
    """Captures pre-delete audit state."""
    logger.warning(f"Signal caught: AccountsAndAcademicsSuite [{instance.id}] deletion requested.")
