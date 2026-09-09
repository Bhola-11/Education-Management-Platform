"""
Django Admin Configuration for Analytics: Enterprise Export Pipeline
"""

from django.contrib import admin
from analytics.models_analytics_export_pipeline import (
    AnalyticsExportPipelineMaster, AnalyticsExportPipelineConfiguration, AnalyticsExportPipelineLedger,
    AnalyticsExportPipelineAuditTransaction, AnalyticsExportPipelineScheduleMatrix, AnalyticsExportPipelineEvaluationMetric,
    AnalyticsExportPipelineRosterMapping, AnalyticsExportPipelineVerificationSignature, AnalyticsExportPipelineNotificationRule,
    AnalyticsExportPipelineAnalyticalSnapshot, AnalyticsExportPipelineComplianceLog, AnalyticsExportPipelineIntegrationBridge,
    AnalyticsExportPipelineSecurityPermit, AnalyticsExportPipelineDocumentAttachment, AnalyticsExportPipelineLifecycleTransition
)

@admin.register(AnalyticsExportPipelineMaster)
class AnalyticsExportPipelineMasterAdmin(admin.ModelAdmin):
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

@admin.register(AnalyticsExportPipelineConfiguration)
class AnalyticsExportPipelineConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AnalyticsExportPipelineAuditTransaction)
class AnalyticsExportPipelineAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AnalyticsExportPipelineLedger)
class AnalyticsExportPipelineLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AnalyticsExportPipelineScheduleMatrix)
class AnalyticsExportPipelineScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AnalyticsExportPipelineEvaluationMetric)
class AnalyticsExportPipelineEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AnalyticsExportPipelineComplianceLog)
class AnalyticsExportPipelineComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
