"""
Django Admin Configuration for Grading: Rank Lists & Distinctions
"""

from django.contrib import admin
from grading.models_grading_rank_lists import (
    GradingRankListsMaster, GradingRankListsConfiguration, GradingRankListsLedger,
    GradingRankListsAuditTransaction, GradingRankListsScheduleMatrix, GradingRankListsEvaluationMetric,
    GradingRankListsRosterMapping, GradingRankListsVerificationSignature, GradingRankListsNotificationRule,
    GradingRankListsAnalyticalSnapshot, GradingRankListsComplianceLog, GradingRankListsIntegrationBridge,
    GradingRankListsSecurityPermit, GradingRankListsDocumentAttachment, GradingRankListsLifecycleTransition
)

@admin.register(GradingRankListsMaster)
class GradingRankListsMasterAdmin(admin.ModelAdmin):
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

@admin.register(GradingRankListsConfiguration)
class GradingRankListsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(GradingRankListsAuditTransaction)
class GradingRankListsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(GradingRankListsLedger)
class GradingRankListsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(GradingRankListsScheduleMatrix)
class GradingRankListsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(GradingRankListsEvaluationMetric)
class GradingRankListsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(GradingRankListsComplianceLog)
class GradingRankListsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
