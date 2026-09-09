"""
Django Admin Configuration for Dashboards: Librarian Ops Hub
"""

from django.contrib import admin
from dashboards.models_dashboards_librarian import (
    DashboardsLibrarianMaster, DashboardsLibrarianConfiguration, DashboardsLibrarianLedger,
    DashboardsLibrarianAuditTransaction, DashboardsLibrarianScheduleMatrix, DashboardsLibrarianEvaluationMetric,
    DashboardsLibrarianRosterMapping, DashboardsLibrarianVerificationSignature, DashboardsLibrarianNotificationRule,
    DashboardsLibrarianAnalyticalSnapshot, DashboardsLibrarianComplianceLog, DashboardsLibrarianIntegrationBridge,
    DashboardsLibrarianSecurityPermit, DashboardsLibrarianDocumentAttachment, DashboardsLibrarianLifecycleTransition
)

@admin.register(DashboardsLibrarianMaster)
class DashboardsLibrarianMasterAdmin(admin.ModelAdmin):
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

@admin.register(DashboardsLibrarianConfiguration)
class DashboardsLibrarianConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(DashboardsLibrarianAuditTransaction)
class DashboardsLibrarianAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(DashboardsLibrarianLedger)
class DashboardsLibrarianLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(DashboardsLibrarianScheduleMatrix)
class DashboardsLibrarianScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(DashboardsLibrarianEvaluationMetric)
class DashboardsLibrarianEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(DashboardsLibrarianComplianceLog)
class DashboardsLibrarianComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
