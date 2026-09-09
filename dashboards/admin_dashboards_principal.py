"""
Django Admin Configuration for Dashboards: Dean Academic Dashboard
"""

from django.contrib import admin
from dashboards.models_dashboards_principal import (
    DashboardsPrincipalMaster, DashboardsPrincipalConfiguration, DashboardsPrincipalLedger,
    DashboardsPrincipalAuditTransaction, DashboardsPrincipalScheduleMatrix, DashboardsPrincipalEvaluationMetric,
    DashboardsPrincipalRosterMapping, DashboardsPrincipalVerificationSignature, DashboardsPrincipalNotificationRule,
    DashboardsPrincipalAnalyticalSnapshot, DashboardsPrincipalComplianceLog, DashboardsPrincipalIntegrationBridge,
    DashboardsPrincipalSecurityPermit, DashboardsPrincipalDocumentAttachment, DashboardsPrincipalLifecycleTransition
)

@admin.register(DashboardsPrincipalMaster)
class DashboardsPrincipalMasterAdmin(admin.ModelAdmin):
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

@admin.register(DashboardsPrincipalConfiguration)
class DashboardsPrincipalConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(DashboardsPrincipalAuditTransaction)
class DashboardsPrincipalAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(DashboardsPrincipalLedger)
class DashboardsPrincipalLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(DashboardsPrincipalScheduleMatrix)
class DashboardsPrincipalScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(DashboardsPrincipalEvaluationMetric)
class DashboardsPrincipalEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(DashboardsPrincipalComplianceLog)
class DashboardsPrincipalComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
