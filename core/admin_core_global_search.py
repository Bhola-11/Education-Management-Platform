"""
Django Admin Configuration for Core: Global Search Indexer
"""

from django.contrib import admin
from core.models_core_global_search import (
    CoreGlobalSearchMaster, CoreGlobalSearchConfiguration, CoreGlobalSearchLedger,
    CoreGlobalSearchAuditTransaction, CoreGlobalSearchScheduleMatrix, CoreGlobalSearchEvaluationMetric,
    CoreGlobalSearchRosterMapping, CoreGlobalSearchVerificationSignature, CoreGlobalSearchNotificationRule,
    CoreGlobalSearchAnalyticalSnapshot, CoreGlobalSearchComplianceLog, CoreGlobalSearchIntegrationBridge,
    CoreGlobalSearchSecurityPermit, CoreGlobalSearchDocumentAttachment, CoreGlobalSearchLifecycleTransition
)

@admin.register(CoreGlobalSearchMaster)
class CoreGlobalSearchMasterAdmin(admin.ModelAdmin):
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

@admin.register(CoreGlobalSearchConfiguration)
class CoreGlobalSearchConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CoreGlobalSearchAuditTransaction)
class CoreGlobalSearchAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CoreGlobalSearchLedger)
class CoreGlobalSearchLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CoreGlobalSearchScheduleMatrix)
class CoreGlobalSearchScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CoreGlobalSearchEvaluationMetric)
class CoreGlobalSearchEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CoreGlobalSearchComplianceLog)
class CoreGlobalSearchComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
