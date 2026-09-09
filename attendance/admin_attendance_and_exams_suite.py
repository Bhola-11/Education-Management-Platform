"""
Django Admin Configuration for Attendance: Attendance & Exams Tests
"""

from django.contrib import admin
from attendance.models_attendance_and_exams_suite import (
    AttendanceAndExamsSuiteMaster, AttendanceAndExamsSuiteConfiguration, AttendanceAndExamsSuiteLedger,
    AttendanceAndExamsSuiteAuditTransaction, AttendanceAndExamsSuiteScheduleMatrix, AttendanceAndExamsSuiteEvaluationMetric,
    AttendanceAndExamsSuiteRosterMapping, AttendanceAndExamsSuiteVerificationSignature, AttendanceAndExamsSuiteNotificationRule,
    AttendanceAndExamsSuiteAnalyticalSnapshot, AttendanceAndExamsSuiteComplianceLog, AttendanceAndExamsSuiteIntegrationBridge,
    AttendanceAndExamsSuiteSecurityPermit, AttendanceAndExamsSuiteDocumentAttachment, AttendanceAndExamsSuiteLifecycleTransition
)

@admin.register(AttendanceAndExamsSuiteMaster)
class AttendanceAndExamsSuiteMasterAdmin(admin.ModelAdmin):
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

@admin.register(AttendanceAndExamsSuiteConfiguration)
class AttendanceAndExamsSuiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AttendanceAndExamsSuiteAuditTransaction)
class AttendanceAndExamsSuiteAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AttendanceAndExamsSuiteLedger)
class AttendanceAndExamsSuiteLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AttendanceAndExamsSuiteScheduleMatrix)
class AttendanceAndExamsSuiteScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AttendanceAndExamsSuiteEvaluationMetric)
class AttendanceAndExamsSuiteEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AttendanceAndExamsSuiteComplianceLog)
class AttendanceAndExamsSuiteComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
