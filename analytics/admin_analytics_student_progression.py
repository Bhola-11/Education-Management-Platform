"""
Django Admin Configuration for Analytics: Student Retention Analytics
"""

from django.contrib import admin
from analytics.models_analytics_student_progression import (
    AnalyticsStudentProgressionMaster, AnalyticsStudentProgressionConfiguration, AnalyticsStudentProgressionLedger,
    AnalyticsStudentProgressionAuditTransaction, AnalyticsStudentProgressionScheduleMatrix, AnalyticsStudentProgressionEvaluationMetric,
    AnalyticsStudentProgressionRosterMapping, AnalyticsStudentProgressionVerificationSignature, AnalyticsStudentProgressionNotificationRule,
    AnalyticsStudentProgressionAnalyticalSnapshot, AnalyticsStudentProgressionComplianceLog, AnalyticsStudentProgressionIntegrationBridge,
    AnalyticsStudentProgressionSecurityPermit, AnalyticsStudentProgressionDocumentAttachment, AnalyticsStudentProgressionLifecycleTransition
)

@admin.register(AnalyticsStudentProgressionMaster)
class AnalyticsStudentProgressionMasterAdmin(admin.ModelAdmin):
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

@admin.register(AnalyticsStudentProgressionConfiguration)
class AnalyticsStudentProgressionConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AnalyticsStudentProgressionAuditTransaction)
class AnalyticsStudentProgressionAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AnalyticsStudentProgressionLedger)
class AnalyticsStudentProgressionLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AnalyticsStudentProgressionScheduleMatrix)
class AnalyticsStudentProgressionScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AnalyticsStudentProgressionEvaluationMetric)
class AnalyticsStudentProgressionEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AnalyticsStudentProgressionComplianceLog)
class AnalyticsStudentProgressionComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
