"""
Django Admin Configuration for Analytics: Attendance Attrition Models
"""

from django.contrib import admin
from analytics.models_analytics_attendance_attrition import (
    AnalyticsAttendanceAttritionMaster, AnalyticsAttendanceAttritionConfiguration, AnalyticsAttendanceAttritionLedger,
    AnalyticsAttendanceAttritionAuditTransaction, AnalyticsAttendanceAttritionScheduleMatrix, AnalyticsAttendanceAttritionEvaluationMetric,
    AnalyticsAttendanceAttritionRosterMapping, AnalyticsAttendanceAttritionVerificationSignature, AnalyticsAttendanceAttritionNotificationRule,
    AnalyticsAttendanceAttritionAnalyticalSnapshot, AnalyticsAttendanceAttritionComplianceLog, AnalyticsAttendanceAttritionIntegrationBridge,
    AnalyticsAttendanceAttritionSecurityPermit, AnalyticsAttendanceAttritionDocumentAttachment, AnalyticsAttendanceAttritionLifecycleTransition
)

@admin.register(AnalyticsAttendanceAttritionMaster)
class AnalyticsAttendanceAttritionMasterAdmin(admin.ModelAdmin):
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

@admin.register(AnalyticsAttendanceAttritionConfiguration)
class AnalyticsAttendanceAttritionConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AnalyticsAttendanceAttritionAuditTransaction)
class AnalyticsAttendanceAttritionAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AnalyticsAttendanceAttritionLedger)
class AnalyticsAttendanceAttritionLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AnalyticsAttendanceAttritionScheduleMatrix)
class AnalyticsAttendanceAttritionScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AnalyticsAttendanceAttritionEvaluationMetric)
class AnalyticsAttendanceAttritionEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AnalyticsAttendanceAttritionComplianceLog)
class AnalyticsAttendanceAttritionComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
