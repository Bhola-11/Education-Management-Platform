"""
Django Admin Configuration for Assignments: Assignment Grading
"""

from django.contrib import admin
from assignments.models_assignments_grading import (
    AssignmentsGradingMaster, AssignmentsGradingConfiguration, AssignmentsGradingLedger,
    AssignmentsGradingAuditTransaction, AssignmentsGradingScheduleMatrix, AssignmentsGradingEvaluationMetric,
    AssignmentsGradingRosterMapping, AssignmentsGradingVerificationSignature, AssignmentsGradingNotificationRule,
    AssignmentsGradingAnalyticalSnapshot, AssignmentsGradingComplianceLog, AssignmentsGradingIntegrationBridge,
    AssignmentsGradingSecurityPermit, AssignmentsGradingDocumentAttachment, AssignmentsGradingLifecycleTransition
)

@admin.register(AssignmentsGradingMaster)
class AssignmentsGradingMasterAdmin(admin.ModelAdmin):
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

@admin.register(AssignmentsGradingConfiguration)
class AssignmentsGradingConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AssignmentsGradingAuditTransaction)
class AssignmentsGradingAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AssignmentsGradingLedger)
class AssignmentsGradingLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AssignmentsGradingScheduleMatrix)
class AssignmentsGradingScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AssignmentsGradingEvaluationMetric)
class AssignmentsGradingEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AssignmentsGradingComplianceLog)
class AssignmentsGradingComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
