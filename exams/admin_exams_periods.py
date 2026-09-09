"""
Django Admin Configuration for Exams: Exam Cycles & Series
"""

from django.contrib import admin
from exams.models_exams_periods import (
    ExamsPeriodsMaster, ExamsPeriodsConfiguration, ExamsPeriodsLedger,
    ExamsPeriodsAuditTransaction, ExamsPeriodsScheduleMatrix, ExamsPeriodsEvaluationMetric,
    ExamsPeriodsRosterMapping, ExamsPeriodsVerificationSignature, ExamsPeriodsNotificationRule,
    ExamsPeriodsAnalyticalSnapshot, ExamsPeriodsComplianceLog, ExamsPeriodsIntegrationBridge,
    ExamsPeriodsSecurityPermit, ExamsPeriodsDocumentAttachment, ExamsPeriodsLifecycleTransition
)

@admin.register(ExamsPeriodsMaster)
class ExamsPeriodsMasterAdmin(admin.ModelAdmin):
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

@admin.register(ExamsPeriodsConfiguration)
class ExamsPeriodsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(ExamsPeriodsAuditTransaction)
class ExamsPeriodsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(ExamsPeriodsLedger)
class ExamsPeriodsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(ExamsPeriodsScheduleMatrix)
class ExamsPeriodsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(ExamsPeriodsEvaluationMetric)
class ExamsPeriodsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(ExamsPeriodsComplianceLog)
class ExamsPeriodsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
