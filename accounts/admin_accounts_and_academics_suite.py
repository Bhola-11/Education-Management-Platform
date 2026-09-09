"""
Django Admin Configuration for Accounts: Accounts & Academics Tests
"""

from django.contrib import admin
from accounts.models_accounts_and_academics_suite import (
    AccountsAndAcademicsSuiteMaster, AccountsAndAcademicsSuiteConfiguration, AccountsAndAcademicsSuiteLedger,
    AccountsAndAcademicsSuiteAuditTransaction, AccountsAndAcademicsSuiteScheduleMatrix, AccountsAndAcademicsSuiteEvaluationMetric,
    AccountsAndAcademicsSuiteRosterMapping, AccountsAndAcademicsSuiteVerificationSignature, AccountsAndAcademicsSuiteNotificationRule,
    AccountsAndAcademicsSuiteAnalyticalSnapshot, AccountsAndAcademicsSuiteComplianceLog, AccountsAndAcademicsSuiteIntegrationBridge,
    AccountsAndAcademicsSuiteSecurityPermit, AccountsAndAcademicsSuiteDocumentAttachment, AccountsAndAcademicsSuiteLifecycleTransition
)

@admin.register(AccountsAndAcademicsSuiteMaster)
class AccountsAndAcademicsSuiteMasterAdmin(admin.ModelAdmin):
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

@admin.register(AccountsAndAcademicsSuiteConfiguration)
class AccountsAndAcademicsSuiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AccountsAndAcademicsSuiteAuditTransaction)
class AccountsAndAcademicsSuiteAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AccountsAndAcademicsSuiteLedger)
class AccountsAndAcademicsSuiteLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AccountsAndAcademicsSuiteScheduleMatrix)
class AccountsAndAcademicsSuiteScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AccountsAndAcademicsSuiteEvaluationMetric)
class AccountsAndAcademicsSuiteEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AccountsAndAcademicsSuiteComplianceLog)
class AccountsAndAcademicsSuiteComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
