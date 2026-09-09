"""
Django Admin Configuration for Grading: Grading & Fees Tests
"""

from django.contrib import admin
from grading.models_grading_and_fees_suite import (
    GradingAndFeesSuiteMaster, GradingAndFeesSuiteConfiguration, GradingAndFeesSuiteLedger,
    GradingAndFeesSuiteAuditTransaction, GradingAndFeesSuiteScheduleMatrix, GradingAndFeesSuiteEvaluationMetric,
    GradingAndFeesSuiteRosterMapping, GradingAndFeesSuiteVerificationSignature, GradingAndFeesSuiteNotificationRule,
    GradingAndFeesSuiteAnalyticalSnapshot, GradingAndFeesSuiteComplianceLog, GradingAndFeesSuiteIntegrationBridge,
    GradingAndFeesSuiteSecurityPermit, GradingAndFeesSuiteDocumentAttachment, GradingAndFeesSuiteLifecycleTransition
)

@admin.register(GradingAndFeesSuiteMaster)
class GradingAndFeesSuiteMasterAdmin(admin.ModelAdmin):
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

@admin.register(GradingAndFeesSuiteConfiguration)
class GradingAndFeesSuiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(GradingAndFeesSuiteAuditTransaction)
class GradingAndFeesSuiteAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(GradingAndFeesSuiteLedger)
class GradingAndFeesSuiteLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(GradingAndFeesSuiteScheduleMatrix)
class GradingAndFeesSuiteScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(GradingAndFeesSuiteEvaluationMetric)
class GradingAndFeesSuiteEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(GradingAndFeesSuiteComplianceLog)
class GradingAndFeesSuiteComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
