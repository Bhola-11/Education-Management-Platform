"""
Django Admin Configuration for Attendance: Period Attendance
"""

from django.contrib import admin
from attendance.models_attendance_period_level import (
    AttendancePeriodLevelMaster, AttendancePeriodLevelConfiguration, AttendancePeriodLevelLedger,
    AttendancePeriodLevelAuditTransaction, AttendancePeriodLevelScheduleMatrix, AttendancePeriodLevelEvaluationMetric,
    AttendancePeriodLevelRosterMapping, AttendancePeriodLevelVerificationSignature, AttendancePeriodLevelNotificationRule,
    AttendancePeriodLevelAnalyticalSnapshot, AttendancePeriodLevelComplianceLog, AttendancePeriodLevelIntegrationBridge,
    AttendancePeriodLevelSecurityPermit, AttendancePeriodLevelDocumentAttachment, AttendancePeriodLevelLifecycleTransition
)

@admin.register(AttendancePeriodLevelMaster)
class AttendancePeriodLevelMasterAdmin(admin.ModelAdmin):
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

@admin.register(AttendancePeriodLevelConfiguration)
class AttendancePeriodLevelConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AttendancePeriodLevelAuditTransaction)
class AttendancePeriodLevelAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AttendancePeriodLevelLedger)
class AttendancePeriodLevelLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AttendancePeriodLevelScheduleMatrix)
class AttendancePeriodLevelScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AttendancePeriodLevelEvaluationMetric)
class AttendancePeriodLevelEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AttendancePeriodLevelComplianceLog)
class AttendancePeriodLevelComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
