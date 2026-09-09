"""
Django Admin Configuration for Fees: Scholarships & Waivers
"""

from django.contrib import admin
from fees.models_fees_scholarships import (
    FeesScholarshipsMaster, FeesScholarshipsConfiguration, FeesScholarshipsLedger,
    FeesScholarshipsAuditTransaction, FeesScholarshipsScheduleMatrix, FeesScholarshipsEvaluationMetric,
    FeesScholarshipsRosterMapping, FeesScholarshipsVerificationSignature, FeesScholarshipsNotificationRule,
    FeesScholarshipsAnalyticalSnapshot, FeesScholarshipsComplianceLog, FeesScholarshipsIntegrationBridge,
    FeesScholarshipsSecurityPermit, FeesScholarshipsDocumentAttachment, FeesScholarshipsLifecycleTransition
)

@admin.register(FeesScholarshipsMaster)
class FeesScholarshipsMasterAdmin(admin.ModelAdmin):
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

@admin.register(FeesScholarshipsConfiguration)
class FeesScholarshipsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(FeesScholarshipsAuditTransaction)
class FeesScholarshipsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(FeesScholarshipsLedger)
class FeesScholarshipsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(FeesScholarshipsScheduleMatrix)
class FeesScholarshipsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(FeesScholarshipsEvaluationMetric)
class FeesScholarshipsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(FeesScholarshipsComplianceLog)
class FeesScholarshipsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
