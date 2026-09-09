"""
Django Admin Configuration for Grading: GPA/CGPA Calculation
"""

from django.contrib import admin
from grading.models_grading_gpa_engine import (
    GradingGpaEngineMaster, GradingGpaEngineConfiguration, GradingGpaEngineLedger,
    GradingGpaEngineAuditTransaction, GradingGpaEngineScheduleMatrix, GradingGpaEngineEvaluationMetric,
    GradingGpaEngineRosterMapping, GradingGpaEngineVerificationSignature, GradingGpaEngineNotificationRule,
    GradingGpaEngineAnalyticalSnapshot, GradingGpaEngineComplianceLog, GradingGpaEngineIntegrationBridge,
    GradingGpaEngineSecurityPermit, GradingGpaEngineDocumentAttachment, GradingGpaEngineLifecycleTransition
)

@admin.register(GradingGpaEngineMaster)
class GradingGpaEngineMasterAdmin(admin.ModelAdmin):
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

@admin.register(GradingGpaEngineConfiguration)
class GradingGpaEngineConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(GradingGpaEngineAuditTransaction)
class GradingGpaEngineAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(GradingGpaEngineLedger)
class GradingGpaEngineLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(GradingGpaEngineScheduleMatrix)
class GradingGpaEngineScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(GradingGpaEngineEvaluationMetric)
class GradingGpaEngineEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(GradingGpaEngineComplianceLog)
class GradingGpaEngineComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
