"""
Django Admin Configuration for Dashboards: Student Self-Service Hub
"""

from django.contrib import admin
from dashboards.models_dashboards_student import (
    DashboardsStudentMaster, DashboardsStudentConfiguration, DashboardsStudentLedger,
    DashboardsStudentAuditTransaction, DashboardsStudentScheduleMatrix, DashboardsStudentEvaluationMetric,
    DashboardsStudentRosterMapping, DashboardsStudentVerificationSignature, DashboardsStudentNotificationRule,
    DashboardsStudentAnalyticalSnapshot, DashboardsStudentComplianceLog, DashboardsStudentIntegrationBridge,
    DashboardsStudentSecurityPermit, DashboardsStudentDocumentAttachment, DashboardsStudentLifecycleTransition
)

@admin.register(DashboardsStudentMaster)
class DashboardsStudentMasterAdmin(admin.ModelAdmin):
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

@admin.register(DashboardsStudentConfiguration)
class DashboardsStudentConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(DashboardsStudentAuditTransaction)
class DashboardsStudentAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(DashboardsStudentLedger)
class DashboardsStudentLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(DashboardsStudentScheduleMatrix)
class DashboardsStudentScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(DashboardsStudentEvaluationMetric)
class DashboardsStudentEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(DashboardsStudentComplianceLog)
class DashboardsStudentComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
