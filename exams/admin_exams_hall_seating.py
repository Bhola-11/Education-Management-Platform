"""
Django Admin Configuration for Exams: Exam Seating Matrix
"""

from django.contrib import admin
from exams.models_exams_hall_seating import (
    ExamsHallSeatingMaster, ExamsHallSeatingConfiguration, ExamsHallSeatingLedger,
    ExamsHallSeatingAuditTransaction, ExamsHallSeatingScheduleMatrix, ExamsHallSeatingEvaluationMetric,
    ExamsHallSeatingRosterMapping, ExamsHallSeatingVerificationSignature, ExamsHallSeatingNotificationRule,
    ExamsHallSeatingAnalyticalSnapshot, ExamsHallSeatingComplianceLog, ExamsHallSeatingIntegrationBridge,
    ExamsHallSeatingSecurityPermit, ExamsHallSeatingDocumentAttachment, ExamsHallSeatingLifecycleTransition
)

@admin.register(ExamsHallSeatingMaster)
class ExamsHallSeatingMasterAdmin(admin.ModelAdmin):
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

@admin.register(ExamsHallSeatingConfiguration)
class ExamsHallSeatingConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(ExamsHallSeatingAuditTransaction)
class ExamsHallSeatingAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(ExamsHallSeatingLedger)
class ExamsHallSeatingLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(ExamsHallSeatingScheduleMatrix)
class ExamsHallSeatingScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(ExamsHallSeatingEvaluationMetric)
class ExamsHallSeatingEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(ExamsHallSeatingComplianceLog)
class ExamsHallSeatingComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
