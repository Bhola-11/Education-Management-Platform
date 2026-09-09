"""
Django Admin Configuration for Analytics: Institutional Financial Analytics
"""

from django.contrib import admin
from analytics.models_analytics_financial import (
    AnalyticsFinancialMaster, AnalyticsFinancialConfiguration, AnalyticsFinancialLedger,
    AnalyticsFinancialAuditTransaction, AnalyticsFinancialScheduleMatrix, AnalyticsFinancialEvaluationMetric,
    AnalyticsFinancialRosterMapping, AnalyticsFinancialVerificationSignature, AnalyticsFinancialNotificationRule,
    AnalyticsFinancialAnalyticalSnapshot, AnalyticsFinancialComplianceLog, AnalyticsFinancialIntegrationBridge,
    AnalyticsFinancialSecurityPermit, AnalyticsFinancialDocumentAttachment, AnalyticsFinancialLifecycleTransition
)

@admin.register(AnalyticsFinancialMaster)
class AnalyticsFinancialMasterAdmin(admin.ModelAdmin):
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

@admin.register(AnalyticsFinancialConfiguration)
class AnalyticsFinancialConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AnalyticsFinancialAuditTransaction)
class AnalyticsFinancialAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AnalyticsFinancialLedger)
class AnalyticsFinancialLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AnalyticsFinancialScheduleMatrix)
class AnalyticsFinancialScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AnalyticsFinancialEvaluationMetric)
class AnalyticsFinancialEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AnalyticsFinancialComplianceLog)
class AnalyticsFinancialComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
