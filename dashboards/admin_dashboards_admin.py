"""
Django Admin Configuration for Dashboards: Executive Dashboard
"""

from django.contrib import admin
from dashboards.models_dashboards_admin import (
    DashboardsAdminMaster, DashboardsAdminConfiguration, DashboardsAdminLedger,
    DashboardsAdminAuditTransaction, DashboardsAdminScheduleMatrix, DashboardsAdminEvaluationMetric,
    DashboardsAdminRosterMapping, DashboardsAdminVerificationSignature, DashboardsAdminNotificationRule,
    DashboardsAdminAnalyticalSnapshot, DashboardsAdminComplianceLog, DashboardsAdminIntegrationBridge,
    DashboardsAdminSecurityPermit, DashboardsAdminDocumentAttachment, DashboardsAdminLifecycleTransition
)

@admin.register(DashboardsAdminMaster)
class DashboardsAdminMasterAdmin(admin.ModelAdmin):
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

@admin.register(DashboardsAdminConfiguration)
class DashboardsAdminConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(DashboardsAdminAuditTransaction)
class DashboardsAdminAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(DashboardsAdminLedger)
class DashboardsAdminLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(DashboardsAdminScheduleMatrix)
class DashboardsAdminScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(DashboardsAdminEvaluationMetric)
class DashboardsAdminEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(DashboardsAdminComplianceLog)
class DashboardsAdminComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
