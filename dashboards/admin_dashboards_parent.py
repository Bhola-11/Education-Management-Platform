"""
Django Admin Configuration for Dashboards: Parent Family Portal
"""

from django.contrib import admin
from dashboards.models_dashboards_parent import (
    DashboardsParentMaster, DashboardsParentConfiguration, DashboardsParentLedger,
    DashboardsParentAuditTransaction, DashboardsParentScheduleMatrix, DashboardsParentEvaluationMetric,
    DashboardsParentRosterMapping, DashboardsParentVerificationSignature, DashboardsParentNotificationRule,
    DashboardsParentAnalyticalSnapshot, DashboardsParentComplianceLog, DashboardsParentIntegrationBridge,
    DashboardsParentSecurityPermit, DashboardsParentDocumentAttachment, DashboardsParentLifecycleTransition
)

@admin.register(DashboardsParentMaster)
class DashboardsParentMasterAdmin(admin.ModelAdmin):
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

@admin.register(DashboardsParentConfiguration)
class DashboardsParentConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(DashboardsParentAuditTransaction)
class DashboardsParentAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(DashboardsParentLedger)
class DashboardsParentLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(DashboardsParentScheduleMatrix)
class DashboardsParentScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(DashboardsParentEvaluationMetric)
class DashboardsParentEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(DashboardsParentComplianceLog)
class DashboardsParentComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
