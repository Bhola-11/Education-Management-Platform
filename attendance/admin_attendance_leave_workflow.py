"""
Django Admin Configuration for Attendance: Leave Workflow
"""

from django.contrib import admin
from attendance.models_attendance_leave_workflow import (
    AttendanceLeaveWorkflowMaster, AttendanceLeaveWorkflowConfiguration, AttendanceLeaveWorkflowLedger,
    AttendanceLeaveWorkflowAuditTransaction, AttendanceLeaveWorkflowScheduleMatrix, AttendanceLeaveWorkflowEvaluationMetric,
    AttendanceLeaveWorkflowRosterMapping, AttendanceLeaveWorkflowVerificationSignature, AttendanceLeaveWorkflowNotificationRule,
    AttendanceLeaveWorkflowAnalyticalSnapshot, AttendanceLeaveWorkflowComplianceLog, AttendanceLeaveWorkflowIntegrationBridge,
    AttendanceLeaveWorkflowSecurityPermit, AttendanceLeaveWorkflowDocumentAttachment, AttendanceLeaveWorkflowLifecycleTransition
)

@admin.register(AttendanceLeaveWorkflowMaster)
class AttendanceLeaveWorkflowMasterAdmin(admin.ModelAdmin):
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

@admin.register(AttendanceLeaveWorkflowConfiguration)
class AttendanceLeaveWorkflowConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AttendanceLeaveWorkflowAuditTransaction)
class AttendanceLeaveWorkflowAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AttendanceLeaveWorkflowLedger)
class AttendanceLeaveWorkflowLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AttendanceLeaveWorkflowScheduleMatrix)
class AttendanceLeaveWorkflowScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AttendanceLeaveWorkflowEvaluationMetric)
class AttendanceLeaveWorkflowEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AttendanceLeaveWorkflowComplianceLog)
class AttendanceLeaveWorkflowComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
