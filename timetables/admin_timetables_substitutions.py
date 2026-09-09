"""
Django Admin Configuration for Timetables: Faculty Substitutions
"""

from django.contrib import admin
from timetables.models_timetables_substitutions import (
    TimetablesSubstitutionsMaster, TimetablesSubstitutionsConfiguration, TimetablesSubstitutionsLedger,
    TimetablesSubstitutionsAuditTransaction, TimetablesSubstitutionsScheduleMatrix, TimetablesSubstitutionsEvaluationMetric,
    TimetablesSubstitutionsRosterMapping, TimetablesSubstitutionsVerificationSignature, TimetablesSubstitutionsNotificationRule,
    TimetablesSubstitutionsAnalyticalSnapshot, TimetablesSubstitutionsComplianceLog, TimetablesSubstitutionsIntegrationBridge,
    TimetablesSubstitutionsSecurityPermit, TimetablesSubstitutionsDocumentAttachment, TimetablesSubstitutionsLifecycleTransition
)

@admin.register(TimetablesSubstitutionsMaster)
class TimetablesSubstitutionsMasterAdmin(admin.ModelAdmin):
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

@admin.register(TimetablesSubstitutionsConfiguration)
class TimetablesSubstitutionsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(TimetablesSubstitutionsAuditTransaction)
class TimetablesSubstitutionsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(TimetablesSubstitutionsLedger)
class TimetablesSubstitutionsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(TimetablesSubstitutionsScheduleMatrix)
class TimetablesSubstitutionsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(TimetablesSubstitutionsEvaluationMetric)
class TimetablesSubstitutionsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(TimetablesSubstitutionsComplianceLog)
class TimetablesSubstitutionsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
