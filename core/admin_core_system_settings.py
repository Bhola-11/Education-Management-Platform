"""
Django Admin Configuration for Core: Institutional Settings
"""

from django.contrib import admin
from core.models_core_system_settings import (
    CoreSystemSettingsMaster, CoreSystemSettingsConfiguration, CoreSystemSettingsLedger,
    CoreSystemSettingsAuditTransaction, CoreSystemSettingsScheduleMatrix, CoreSystemSettingsEvaluationMetric,
    CoreSystemSettingsRosterMapping, CoreSystemSettingsVerificationSignature, CoreSystemSettingsNotificationRule,
    CoreSystemSettingsAnalyticalSnapshot, CoreSystemSettingsComplianceLog, CoreSystemSettingsIntegrationBridge,
    CoreSystemSettingsSecurityPermit, CoreSystemSettingsDocumentAttachment, CoreSystemSettingsLifecycleTransition
)

@admin.register(CoreSystemSettingsMaster)
class CoreSystemSettingsMasterAdmin(admin.ModelAdmin):
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

@admin.register(CoreSystemSettingsConfiguration)
class CoreSystemSettingsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CoreSystemSettingsAuditTransaction)
class CoreSystemSettingsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CoreSystemSettingsLedger)
class CoreSystemSettingsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CoreSystemSettingsScheduleMatrix)
class CoreSystemSettingsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CoreSystemSettingsEvaluationMetric)
class CoreSystemSettingsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CoreSystemSettingsComplianceLog)
class CoreSystemSettingsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
