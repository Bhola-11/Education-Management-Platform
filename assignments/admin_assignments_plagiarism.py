"""
Django Admin Configuration for Assignments: Academic Integrity
"""

from django.contrib import admin
from assignments.models_assignments_plagiarism import (
    AssignmentsPlagiarismMaster, AssignmentsPlagiarismConfiguration, AssignmentsPlagiarismLedger,
    AssignmentsPlagiarismAuditTransaction, AssignmentsPlagiarismScheduleMatrix, AssignmentsPlagiarismEvaluationMetric,
    AssignmentsPlagiarismRosterMapping, AssignmentsPlagiarismVerificationSignature, AssignmentsPlagiarismNotificationRule,
    AssignmentsPlagiarismAnalyticalSnapshot, AssignmentsPlagiarismComplianceLog, AssignmentsPlagiarismIntegrationBridge,
    AssignmentsPlagiarismSecurityPermit, AssignmentsPlagiarismDocumentAttachment, AssignmentsPlagiarismLifecycleTransition
)

@admin.register(AssignmentsPlagiarismMaster)
class AssignmentsPlagiarismMasterAdmin(admin.ModelAdmin):
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

@admin.register(AssignmentsPlagiarismConfiguration)
class AssignmentsPlagiarismConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AssignmentsPlagiarismAuditTransaction)
class AssignmentsPlagiarismAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AssignmentsPlagiarismLedger)
class AssignmentsPlagiarismLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AssignmentsPlagiarismScheduleMatrix)
class AssignmentsPlagiarismScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AssignmentsPlagiarismEvaluationMetric)
class AssignmentsPlagiarismEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AssignmentsPlagiarismComplianceLog)
class AssignmentsPlagiarismComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
