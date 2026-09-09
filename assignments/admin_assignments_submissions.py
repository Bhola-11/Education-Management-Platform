"""
Django Admin Configuration for Assignments: Student Submissions
"""

from django.contrib import admin
from assignments.models_assignments_submissions import (
    AssignmentsSubmissionsMaster, AssignmentsSubmissionsConfiguration, AssignmentsSubmissionsLedger,
    AssignmentsSubmissionsAuditTransaction, AssignmentsSubmissionsScheduleMatrix, AssignmentsSubmissionsEvaluationMetric,
    AssignmentsSubmissionsRosterMapping, AssignmentsSubmissionsVerificationSignature, AssignmentsSubmissionsNotificationRule,
    AssignmentsSubmissionsAnalyticalSnapshot, AssignmentsSubmissionsComplianceLog, AssignmentsSubmissionsIntegrationBridge,
    AssignmentsSubmissionsSecurityPermit, AssignmentsSubmissionsDocumentAttachment, AssignmentsSubmissionsLifecycleTransition
)

@admin.register(AssignmentsSubmissionsMaster)
class AssignmentsSubmissionsMasterAdmin(admin.ModelAdmin):
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

@admin.register(AssignmentsSubmissionsConfiguration)
class AssignmentsSubmissionsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AssignmentsSubmissionsAuditTransaction)
class AssignmentsSubmissionsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AssignmentsSubmissionsLedger)
class AssignmentsSubmissionsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AssignmentsSubmissionsScheduleMatrix)
class AssignmentsSubmissionsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AssignmentsSubmissionsEvaluationMetric)
class AssignmentsSubmissionsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AssignmentsSubmissionsComplianceLog)
class AssignmentsSubmissionsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
