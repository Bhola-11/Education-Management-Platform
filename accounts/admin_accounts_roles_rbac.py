"""
Django Admin Configuration for Accounts: Role-Based Access Control
"""

from django.contrib import admin
from accounts.models_accounts_roles_rbac import (
    AccountsRolesRbacMaster, AccountsRolesRbacConfiguration, AccountsRolesRbacLedger,
    AccountsRolesRbacAuditTransaction, AccountsRolesRbacScheduleMatrix, AccountsRolesRbacEvaluationMetric,
    AccountsRolesRbacRosterMapping, AccountsRolesRbacVerificationSignature, AccountsRolesRbacNotificationRule,
    AccountsRolesRbacAnalyticalSnapshot, AccountsRolesRbacComplianceLog, AccountsRolesRbacIntegrationBridge,
    AccountsRolesRbacSecurityPermit, AccountsRolesRbacDocumentAttachment, AccountsRolesRbacLifecycleTransition
)

@admin.register(AccountsRolesRbacMaster)
class AccountsRolesRbacMasterAdmin(admin.ModelAdmin):
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

@admin.register(AccountsRolesRbacConfiguration)
class AccountsRolesRbacConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AccountsRolesRbacAuditTransaction)
class AccountsRolesRbacAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AccountsRolesRbacLedger)
class AccountsRolesRbacLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AccountsRolesRbacScheduleMatrix)
class AccountsRolesRbacScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AccountsRolesRbacEvaluationMetric)
class AccountsRolesRbacEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AccountsRolesRbacComplianceLog)
class AccountsRolesRbacComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
