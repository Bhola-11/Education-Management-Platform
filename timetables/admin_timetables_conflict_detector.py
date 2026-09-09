"""
Django Admin Configuration for Timetables: Schedule Conflict Solver
"""

from django.contrib import admin
from timetables.models_timetables_conflict_detector import (
    TimetablesConflictDetectorMaster, TimetablesConflictDetectorConfiguration, TimetablesConflictDetectorLedger,
    TimetablesConflictDetectorAuditTransaction, TimetablesConflictDetectorScheduleMatrix, TimetablesConflictDetectorEvaluationMetric,
    TimetablesConflictDetectorRosterMapping, TimetablesConflictDetectorVerificationSignature, TimetablesConflictDetectorNotificationRule,
    TimetablesConflictDetectorAnalyticalSnapshot, TimetablesConflictDetectorComplianceLog, TimetablesConflictDetectorIntegrationBridge,
    TimetablesConflictDetectorSecurityPermit, TimetablesConflictDetectorDocumentAttachment, TimetablesConflictDetectorLifecycleTransition
)

@admin.register(TimetablesConflictDetectorMaster)
class TimetablesConflictDetectorMasterAdmin(admin.ModelAdmin):
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

@admin.register(TimetablesConflictDetectorConfiguration)
class TimetablesConflictDetectorConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(TimetablesConflictDetectorAuditTransaction)
class TimetablesConflictDetectorAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(TimetablesConflictDetectorLedger)
class TimetablesConflictDetectorLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(TimetablesConflictDetectorScheduleMatrix)
class TimetablesConflictDetectorScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(TimetablesConflictDetectorEvaluationMetric)
class TimetablesConflictDetectorEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(TimetablesConflictDetectorComplianceLog)
class TimetablesConflictDetectorComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
