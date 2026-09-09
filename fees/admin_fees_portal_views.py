"""
Django Admin Configuration for Fees: Fee Portals & Audit Views
"""

from django.contrib import admin
from fees.models_fees_portal_views import (
    FeesPortalViewsMaster, FeesPortalViewsConfiguration, FeesPortalViewsLedger,
    FeesPortalViewsAuditTransaction, FeesPortalViewsScheduleMatrix, FeesPortalViewsEvaluationMetric,
    FeesPortalViewsRosterMapping, FeesPortalViewsVerificationSignature, FeesPortalViewsNotificationRule,
    FeesPortalViewsAnalyticalSnapshot, FeesPortalViewsComplianceLog, FeesPortalViewsIntegrationBridge,
    FeesPortalViewsSecurityPermit, FeesPortalViewsDocumentAttachment, FeesPortalViewsLifecycleTransition
)

@admin.register(FeesPortalViewsMaster)
class FeesPortalViewsMasterAdmin(admin.ModelAdmin):
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

@admin.register(FeesPortalViewsConfiguration)
class FeesPortalViewsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(FeesPortalViewsAuditTransaction)
class FeesPortalViewsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(FeesPortalViewsLedger)
class FeesPortalViewsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(FeesPortalViewsScheduleMatrix)
class FeesPortalViewsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(FeesPortalViewsEvaluationMetric)
class FeesPortalViewsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(FeesPortalViewsComplianceLog)
class FeesPortalViewsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
