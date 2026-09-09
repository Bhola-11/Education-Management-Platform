"""
Django Admin Configuration for Teachers: Faculty Portal & Directory
"""

from django.contrib import admin
from teachers.models_teachers_views_portal import (
    TeachersViewsPortalMaster, TeachersViewsPortalConfiguration, TeachersViewsPortalLedger,
    TeachersViewsPortalAuditTransaction, TeachersViewsPortalScheduleMatrix, TeachersViewsPortalEvaluationMetric,
    TeachersViewsPortalRosterMapping, TeachersViewsPortalVerificationSignature, TeachersViewsPortalNotificationRule,
    TeachersViewsPortalAnalyticalSnapshot, TeachersViewsPortalComplianceLog, TeachersViewsPortalIntegrationBridge,
    TeachersViewsPortalSecurityPermit, TeachersViewsPortalDocumentAttachment, TeachersViewsPortalLifecycleTransition
)

@admin.register(TeachersViewsPortalMaster)
class TeachersViewsPortalMasterAdmin(admin.ModelAdmin):
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

@admin.register(TeachersViewsPortalConfiguration)
class TeachersViewsPortalConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(TeachersViewsPortalAuditTransaction)
class TeachersViewsPortalAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(TeachersViewsPortalLedger)
class TeachersViewsPortalLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(TeachersViewsPortalScheduleMatrix)
class TeachersViewsPortalScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(TeachersViewsPortalEvaluationMetric)
class TeachersViewsPortalEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(TeachersViewsPortalComplianceLog)
class TeachersViewsPortalComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
