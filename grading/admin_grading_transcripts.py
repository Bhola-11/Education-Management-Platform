"""
Django Admin Configuration for Grading: Official Academic Transcripts
"""

from django.contrib import admin
from grading.models_grading_transcripts import (
    GradingTranscriptsMaster, GradingTranscriptsConfiguration, GradingTranscriptsLedger,
    GradingTranscriptsAuditTransaction, GradingTranscriptsScheduleMatrix, GradingTranscriptsEvaluationMetric,
    GradingTranscriptsRosterMapping, GradingTranscriptsVerificationSignature, GradingTranscriptsNotificationRule,
    GradingTranscriptsAnalyticalSnapshot, GradingTranscriptsComplianceLog, GradingTranscriptsIntegrationBridge,
    GradingTranscriptsSecurityPermit, GradingTranscriptsDocumentAttachment, GradingTranscriptsLifecycleTransition
)

@admin.register(GradingTranscriptsMaster)
class GradingTranscriptsMasterAdmin(admin.ModelAdmin):
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

@admin.register(GradingTranscriptsConfiguration)
class GradingTranscriptsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(GradingTranscriptsAuditTransaction)
class GradingTranscriptsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(GradingTranscriptsLedger)
class GradingTranscriptsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(GradingTranscriptsScheduleMatrix)
class GradingTranscriptsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(GradingTranscriptsEvaluationMetric)
class GradingTranscriptsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(GradingTranscriptsComplianceLog)
class GradingTranscriptsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
