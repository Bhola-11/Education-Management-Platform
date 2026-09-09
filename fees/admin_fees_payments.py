"""
Django Admin Configuration for Fees: Payment Processing
"""

from django.contrib import admin
from fees.models_fees_payments import (
    FeesPaymentsMaster, FeesPaymentsConfiguration, FeesPaymentsLedger,
    FeesPaymentsAuditTransaction, FeesPaymentsScheduleMatrix, FeesPaymentsEvaluationMetric,
    FeesPaymentsRosterMapping, FeesPaymentsVerificationSignature, FeesPaymentsNotificationRule,
    FeesPaymentsAnalyticalSnapshot, FeesPaymentsComplianceLog, FeesPaymentsIntegrationBridge,
    FeesPaymentsSecurityPermit, FeesPaymentsDocumentAttachment, FeesPaymentsLifecycleTransition
)

@admin.register(FeesPaymentsMaster)
class FeesPaymentsMasterAdmin(admin.ModelAdmin):
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

@admin.register(FeesPaymentsConfiguration)
class FeesPaymentsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(FeesPaymentsAuditTransaction)
class FeesPaymentsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(FeesPaymentsLedger)
class FeesPaymentsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(FeesPaymentsScheduleMatrix)
class FeesPaymentsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(FeesPaymentsEvaluationMetric)
class FeesPaymentsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(FeesPaymentsComplianceLog)
class FeesPaymentsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
