"""
Django Admin Configuration for Fees: Late Fee Penalties
"""

from django.contrib import admin
from fees.models_fees_penalties import (
    FeesPenaltiesMaster, FeesPenaltiesConfiguration, FeesPenaltiesLedger,
    FeesPenaltiesAuditTransaction, FeesPenaltiesScheduleMatrix, FeesPenaltiesEvaluationMetric,
    FeesPenaltiesRosterMapping, FeesPenaltiesVerificationSignature, FeesPenaltiesNotificationRule,
    FeesPenaltiesAnalyticalSnapshot, FeesPenaltiesComplianceLog, FeesPenaltiesIntegrationBridge,
    FeesPenaltiesSecurityPermit, FeesPenaltiesDocumentAttachment, FeesPenaltiesLifecycleTransition
)

@admin.register(FeesPenaltiesMaster)
class FeesPenaltiesMasterAdmin(admin.ModelAdmin):
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

@admin.register(FeesPenaltiesConfiguration)
class FeesPenaltiesConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(FeesPenaltiesAuditTransaction)
class FeesPenaltiesAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(FeesPenaltiesLedger)
class FeesPenaltiesLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(FeesPenaltiesScheduleMatrix)
class FeesPenaltiesScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(FeesPenaltiesEvaluationMetric)
class FeesPenaltiesEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(FeesPenaltiesComplianceLog)
class FeesPenaltiesComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
