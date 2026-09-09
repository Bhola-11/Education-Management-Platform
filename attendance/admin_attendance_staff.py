"""
Django Admin Configuration for Attendance: Staff Timekeeping
"""

from django.contrib import admin
from attendance.models_attendance_staff import (
    AttendanceStaffMaster, AttendanceStaffConfiguration, AttendanceStaffLedger,
    AttendanceStaffAuditTransaction, AttendanceStaffScheduleMatrix, AttendanceStaffEvaluationMetric,
    AttendanceStaffRosterMapping, AttendanceStaffVerificationSignature, AttendanceStaffNotificationRule,
    AttendanceStaffAnalyticalSnapshot, AttendanceStaffComplianceLog, AttendanceStaffIntegrationBridge,
    AttendanceStaffSecurityPermit, AttendanceStaffDocumentAttachment, AttendanceStaffLifecycleTransition
)

@admin.register(AttendanceStaffMaster)
class AttendanceStaffMasterAdmin(admin.ModelAdmin):
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

@admin.register(AttendanceStaffConfiguration)
class AttendanceStaffConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AttendanceStaffAuditTransaction)
class AttendanceStaffAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AttendanceStaffLedger)
class AttendanceStaffLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AttendanceStaffScheduleMatrix)
class AttendanceStaffScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AttendanceStaffEvaluationMetric)
class AttendanceStaffEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AttendanceStaffComplianceLog)
class AttendanceStaffComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
