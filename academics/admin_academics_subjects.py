"""
Django Admin Configuration for Academics: Subject Architecture
"""

from django.contrib import admin
from academics.models_academics_subjects import (
    AcademicsSubjectsMaster, AcademicsSubjectsConfiguration, AcademicsSubjectsLedger,
    AcademicsSubjectsAuditTransaction, AcademicsSubjectsScheduleMatrix, AcademicsSubjectsEvaluationMetric,
    AcademicsSubjectsRosterMapping, AcademicsSubjectsVerificationSignature, AcademicsSubjectsNotificationRule,
    AcademicsSubjectsAnalyticalSnapshot, AcademicsSubjectsComplianceLog, AcademicsSubjectsIntegrationBridge,
    AcademicsSubjectsSecurityPermit, AcademicsSubjectsDocumentAttachment, AcademicsSubjectsLifecycleTransition
)

@admin.register(AcademicsSubjectsMaster)
class AcademicsSubjectsMasterAdmin(admin.ModelAdmin):
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

@admin.register(AcademicsSubjectsConfiguration)
class AcademicsSubjectsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AcademicsSubjectsAuditTransaction)
class AcademicsSubjectsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AcademicsSubjectsLedger)
class AcademicsSubjectsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AcademicsSubjectsScheduleMatrix)
class AcademicsSubjectsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AcademicsSubjectsEvaluationMetric)
class AcademicsSubjectsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AcademicsSubjectsComplianceLog)
class AcademicsSubjectsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
