"""
Django Admin Configuration for Dashboards: Bursar Financial Hub
"""

from django.contrib import admin
from dashboards.models_dashboards_finance import (
    DashboardsFinanceMaster, DashboardsFinanceConfiguration, DashboardsFinanceLedger,
    DashboardsFinanceAuditTransaction, DashboardsFinanceScheduleMatrix, DashboardsFinanceEvaluationMetric,
    DashboardsFinanceRosterMapping, DashboardsFinanceVerificationSignature, DashboardsFinanceNotificationRule,
    DashboardsFinanceAnalyticalSnapshot, DashboardsFinanceComplianceLog, DashboardsFinanceIntegrationBridge,
    DashboardsFinanceSecurityPermit, DashboardsFinanceDocumentAttachment, DashboardsFinanceLifecycleTransition
)

@admin.register(DashboardsFinanceMaster)
class DashboardsFinanceMasterAdmin(admin.ModelAdmin):
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

@admin.register(DashboardsFinanceConfiguration)
class DashboardsFinanceConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(DashboardsFinanceAuditTransaction)
class DashboardsFinanceAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(DashboardsFinanceLedger)
class DashboardsFinanceLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(DashboardsFinanceScheduleMatrix)
class DashboardsFinanceScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(DashboardsFinanceEvaluationMetric)
class DashboardsFinanceEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(DashboardsFinanceComplianceLog)
class DashboardsFinanceComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
