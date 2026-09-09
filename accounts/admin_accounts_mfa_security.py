"""
Django Admin Configuration for Accounts: MFA & Security
"""

from django.contrib import admin
from accounts.models_accounts_mfa_security import (
    AccountsMfaSecurityMaster, AccountsMfaSecurityConfiguration, AccountsMfaSecurityLedger,
    AccountsMfaSecurityAuditTransaction, AccountsMfaSecurityScheduleMatrix, AccountsMfaSecurityEvaluationMetric,
    AccountsMfaSecurityRosterMapping, AccountsMfaSecurityVerificationSignature, AccountsMfaSecurityNotificationRule,
    AccountsMfaSecurityAnalyticalSnapshot, AccountsMfaSecurityComplianceLog, AccountsMfaSecurityIntegrationBridge,
    AccountsMfaSecuritySecurityPermit, AccountsMfaSecurityDocumentAttachment, AccountsMfaSecurityLifecycleTransition
)

@admin.register(AccountsMfaSecurityMaster)
class AccountsMfaSecurityMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "capacity_limit", "allocated_count", "is_active", "effective_date")
    list_filter = ("status", "is_active", "effective_date")
    search_fields = ("code", "name", "description")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basic Identification", {"fields": ("code", "name", "slug", "description")}),
        ("Status & Weights", {"fields": ("priority", "status", "is_active", "is_verified", "is_locked")}),
        ("Quantitative Parameters", {"fields": ("score_rating", "monetary_value", "capacity_limit", "allocated_count")}),
        ("Temporal Controls", {"fields": ("effective_date", "expiration_date")}),
        ("Audit Metadata", {"fields": ("metadata", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

@admin.register(AccountsMfaSecurityConfiguration)
class AccountsMfaSecurityConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AccountsMfaSecurityAuditTransaction)
class AccountsMfaSecurityAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AccountsMfaSecurityLedger)
class AccountsMfaSecurityLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AccountsMfaSecurityScheduleMatrix)
class AccountsMfaSecurityScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AccountsMfaSecurityEvaluationMetric)
class AccountsMfaSecurityEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AccountsMfaSecurityComplianceLog)
class AccountsMfaSecurityComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
