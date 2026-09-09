"""
Django Admin Configuration for Timetables: Timetable Matrix
"""

from django.contrib import admin
from timetables.models_timetables_entry import (
    TimetablesEntryMaster, TimetablesEntryConfiguration, TimetablesEntryLedger,
    TimetablesEntryAuditTransaction, TimetablesEntryScheduleMatrix, TimetablesEntryEvaluationMetric,
    TimetablesEntryRosterMapping, TimetablesEntryVerificationSignature, TimetablesEntryNotificationRule,
    TimetablesEntryAnalyticalSnapshot, TimetablesEntryComplianceLog, TimetablesEntryIntegrationBridge,
    TimetablesEntrySecurityPermit, TimetablesEntryDocumentAttachment, TimetablesEntryLifecycleTransition
)

@admin.register(TimetablesEntryMaster)
class TimetablesEntryMasterAdmin(admin.ModelAdmin):
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

@admin.register(TimetablesEntryConfiguration)
class TimetablesEntryConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(TimetablesEntryAuditTransaction)
class TimetablesEntryAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(TimetablesEntryLedger)
class TimetablesEntryLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(TimetablesEntryScheduleMatrix)
class TimetablesEntryScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(TimetablesEntryEvaluationMetric)
class TimetablesEntryEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(TimetablesEntryComplianceLog)
class TimetablesEntryComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
