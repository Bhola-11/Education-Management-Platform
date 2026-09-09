"""
Django Admin Configuration for Core: Security & Penetration Tests
"""

from django.contrib import admin
from core.models_security_and_permissions_suite import (
    SecurityAndPermissionsSuiteMaster, SecurityAndPermissionsSuiteConfiguration, SecurityAndPermissionsSuiteLedger,
    SecurityAndPermissionsSuiteAuditTransaction, SecurityAndPermissionsSuiteScheduleMatrix, SecurityAndPermissionsSuiteEvaluationMetric,
    SecurityAndPermissionsSuiteRosterMapping, SecurityAndPermissionsSuiteVerificationSignature, SecurityAndPermissionsSuiteNotificationRule,
    SecurityAndPermissionsSuiteAnalyticalSnapshot, SecurityAndPermissionsSuiteComplianceLog, SecurityAndPermissionsSuiteIntegrationBridge,
    SecurityAndPermissionsSuiteSecurityPermit, SecurityAndPermissionsSuiteDocumentAttachment, SecurityAndPermissionsSuiteLifecycleTransition
)

@admin.register(SecurityAndPermissionsSuiteMaster)
class SecurityAndPermissionsSuiteMasterAdmin(admin.ModelAdmin):
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

@admin.register(SecurityAndPermissionsSuiteConfiguration)
class SecurityAndPermissionsSuiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(SecurityAndPermissionsSuiteAuditTransaction)
class SecurityAndPermissionsSuiteAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(SecurityAndPermissionsSuiteLedger)
class SecurityAndPermissionsSuiteLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(SecurityAndPermissionsSuiteScheduleMatrix)
class SecurityAndPermissionsSuiteScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(SecurityAndPermissionsSuiteEvaluationMetric)
class SecurityAndPermissionsSuiteEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(SecurityAndPermissionsSuiteComplianceLog)
class SecurityAndPermissionsSuiteComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
