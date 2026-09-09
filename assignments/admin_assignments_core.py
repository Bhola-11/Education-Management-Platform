"""
Django Admin Configuration for Assignments: Assignment Specifications
"""

from django.contrib import admin
from assignments.models_assignments_core import (
    AssignmentsCoreMaster, AssignmentsCoreConfiguration, AssignmentsCoreLedger,
    AssignmentsCoreAuditTransaction, AssignmentsCoreScheduleMatrix, AssignmentsCoreEvaluationMetric,
    AssignmentsCoreRosterMapping, AssignmentsCoreVerificationSignature, AssignmentsCoreNotificationRule,
    AssignmentsCoreAnalyticalSnapshot, AssignmentsCoreComplianceLog, AssignmentsCoreIntegrationBridge,
    AssignmentsCoreSecurityPermit, AssignmentsCoreDocumentAttachment, AssignmentsCoreLifecycleTransition
)

@admin.register(AssignmentsCoreMaster)
class AssignmentsCoreMasterAdmin(admin.ModelAdmin):
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

@admin.register(AssignmentsCoreConfiguration)
class AssignmentsCoreConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AssignmentsCoreAuditTransaction)
class AssignmentsCoreAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AssignmentsCoreLedger)
class AssignmentsCoreLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AssignmentsCoreScheduleMatrix)
class AssignmentsCoreScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AssignmentsCoreEvaluationMetric)
class AssignmentsCoreEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AssignmentsCoreComplianceLog)
class AssignmentsCoreComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
