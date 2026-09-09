"""
Django Admin Configuration for Accounts: Authentication
"""

from django.contrib import admin
from accounts.models_accounts_custom_user import (
    AccountsCustomUserMaster, AccountsCustomUserConfiguration, AccountsCustomUserLedger,
    AccountsCustomUserAuditTransaction, AccountsCustomUserScheduleMatrix, AccountsCustomUserEvaluationMetric,
    AccountsCustomUserRosterMapping, AccountsCustomUserVerificationSignature, AccountsCustomUserNotificationRule,
    AccountsCustomUserAnalyticalSnapshot, AccountsCustomUserComplianceLog, AccountsCustomUserIntegrationBridge,
    AccountsCustomUserSecurityPermit, AccountsCustomUserDocumentAttachment, AccountsCustomUserLifecycleTransition
)

@admin.register(AccountsCustomUserMaster)
class AccountsCustomUserMasterAdmin(admin.ModelAdmin):
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

@admin.register(AccountsCustomUserConfiguration)
class AccountsCustomUserConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AccountsCustomUserAuditTransaction)
class AccountsCustomUserAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AccountsCustomUserLedger)
class AccountsCustomUserLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AccountsCustomUserScheduleMatrix)
class AccountsCustomUserScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AccountsCustomUserEvaluationMetric)
class AccountsCustomUserEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AccountsCustomUserComplianceLog)
class AccountsCustomUserComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
