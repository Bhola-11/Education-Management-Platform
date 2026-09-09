"""
Django Admin Configuration for Grading: Grade Scales & Rules
"""

from django.contrib import admin
from grading.models_grading_scales import (
    GradingScalesMaster, GradingScalesConfiguration, GradingScalesLedger,
    GradingScalesAuditTransaction, GradingScalesScheduleMatrix, GradingScalesEvaluationMetric,
    GradingScalesRosterMapping, GradingScalesVerificationSignature, GradingScalesNotificationRule,
    GradingScalesAnalyticalSnapshot, GradingScalesComplianceLog, GradingScalesIntegrationBridge,
    GradingScalesSecurityPermit, GradingScalesDocumentAttachment, GradingScalesLifecycleTransition
)

@admin.register(GradingScalesMaster)
class GradingScalesMasterAdmin(admin.ModelAdmin):
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

@admin.register(GradingScalesConfiguration)
class GradingScalesConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(GradingScalesAuditTransaction)
class GradingScalesAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(GradingScalesLedger)
class GradingScalesLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(GradingScalesScheduleMatrix)
class GradingScalesScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(GradingScalesEvaluationMetric)
class GradingScalesEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(GradingScalesComplianceLog)
class GradingScalesComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
