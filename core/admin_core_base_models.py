"""
Django Admin Configuration for Core: Core Architecture
"""

from django.contrib import admin
from core.models_core_base_models import (
    CoreBaseModelsMaster, CoreBaseModelsConfiguration, CoreBaseModelsLedger,
    CoreBaseModelsAuditTransaction, CoreBaseModelsScheduleMatrix, CoreBaseModelsEvaluationMetric,
    CoreBaseModelsRosterMapping, CoreBaseModelsVerificationSignature, CoreBaseModelsNotificationRule,
    CoreBaseModelsAnalyticalSnapshot, CoreBaseModelsComplianceLog, CoreBaseModelsIntegrationBridge,
    CoreBaseModelsSecurityPermit, CoreBaseModelsDocumentAttachment, CoreBaseModelsLifecycleTransition
)

@admin.register(CoreBaseModelsMaster)
class CoreBaseModelsMasterAdmin(admin.ModelAdmin):
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

@admin.register(CoreBaseModelsConfiguration)
class CoreBaseModelsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CoreBaseModelsAuditTransaction)
class CoreBaseModelsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CoreBaseModelsLedger)
class CoreBaseModelsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CoreBaseModelsScheduleMatrix)
class CoreBaseModelsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CoreBaseModelsEvaluationMetric)
class CoreBaseModelsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CoreBaseModelsComplianceLog)
class CoreBaseModelsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
