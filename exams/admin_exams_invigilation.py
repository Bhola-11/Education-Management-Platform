"""
Django Admin Configuration for Exams: Invigilation Roster
"""

from django.contrib import admin
from exams.models_exams_invigilation import (
    ExamsInvigilationMaster, ExamsInvigilationConfiguration, ExamsInvigilationLedger,
    ExamsInvigilationAuditTransaction, ExamsInvigilationScheduleMatrix, ExamsInvigilationEvaluationMetric,
    ExamsInvigilationRosterMapping, ExamsInvigilationVerificationSignature, ExamsInvigilationNotificationRule,
    ExamsInvigilationAnalyticalSnapshot, ExamsInvigilationComplianceLog, ExamsInvigilationIntegrationBridge,
    ExamsInvigilationSecurityPermit, ExamsInvigilationDocumentAttachment, ExamsInvigilationLifecycleTransition
)

@admin.register(ExamsInvigilationMaster)
class ExamsInvigilationMasterAdmin(admin.ModelAdmin):
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

@admin.register(ExamsInvigilationConfiguration)
class ExamsInvigilationConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(ExamsInvigilationAuditTransaction)
class ExamsInvigilationAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(ExamsInvigilationLedger)
class ExamsInvigilationLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(ExamsInvigilationScheduleMatrix)
class ExamsInvigilationScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(ExamsInvigilationEvaluationMetric)
class ExamsInvigilationEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(ExamsInvigilationComplianceLog)
class ExamsInvigilationComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
