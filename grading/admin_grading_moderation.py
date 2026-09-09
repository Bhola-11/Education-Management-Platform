"""
Django Admin Configuration for Grading: Marks Moderation Workflow
"""

from django.contrib import admin
from grading.models_grading_moderation import (
    GradingModerationMaster, GradingModerationConfiguration, GradingModerationLedger,
    GradingModerationAuditTransaction, GradingModerationScheduleMatrix, GradingModerationEvaluationMetric,
    GradingModerationRosterMapping, GradingModerationVerificationSignature, GradingModerationNotificationRule,
    GradingModerationAnalyticalSnapshot, GradingModerationComplianceLog, GradingModerationIntegrationBridge,
    GradingModerationSecurityPermit, GradingModerationDocumentAttachment, GradingModerationLifecycleTransition
)

@admin.register(GradingModerationMaster)
class GradingModerationMasterAdmin(admin.ModelAdmin):
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

@admin.register(GradingModerationConfiguration)
class GradingModerationConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(GradingModerationAuditTransaction)
class GradingModerationAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(GradingModerationLedger)
class GradingModerationLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(GradingModerationScheduleMatrix)
class GradingModerationScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(GradingModerationEvaluationMetric)
class GradingModerationEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(GradingModerationComplianceLog)
class GradingModerationComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
