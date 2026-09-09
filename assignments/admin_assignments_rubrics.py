"""
Django Admin Configuration for Assignments: Evaluation Rubrics
"""

from django.contrib import admin
from assignments.models_assignments_rubrics import (
    AssignmentsRubricsMaster, AssignmentsRubricsConfiguration, AssignmentsRubricsLedger,
    AssignmentsRubricsAuditTransaction, AssignmentsRubricsScheduleMatrix, AssignmentsRubricsEvaluationMetric,
    AssignmentsRubricsRosterMapping, AssignmentsRubricsVerificationSignature, AssignmentsRubricsNotificationRule,
    AssignmentsRubricsAnalyticalSnapshot, AssignmentsRubricsComplianceLog, AssignmentsRubricsIntegrationBridge,
    AssignmentsRubricsSecurityPermit, AssignmentsRubricsDocumentAttachment, AssignmentsRubricsLifecycleTransition
)

@admin.register(AssignmentsRubricsMaster)
class AssignmentsRubricsMasterAdmin(admin.ModelAdmin):
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

@admin.register(AssignmentsRubricsConfiguration)
class AssignmentsRubricsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AssignmentsRubricsAuditTransaction)
class AssignmentsRubricsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AssignmentsRubricsLedger)
class AssignmentsRubricsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AssignmentsRubricsScheduleMatrix)
class AssignmentsRubricsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AssignmentsRubricsEvaluationMetric)
class AssignmentsRubricsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AssignmentsRubricsComplianceLog)
class AssignmentsRubricsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
