"""
Django Admin Configuration for Students: Student Portal & Directory
"""

from django.contrib import admin
from students.models_students_views_portal import (
    StudentsViewsPortalMaster, StudentsViewsPortalConfiguration, StudentsViewsPortalLedger,
    StudentsViewsPortalAuditTransaction, StudentsViewsPortalScheduleMatrix, StudentsViewsPortalEvaluationMetric,
    StudentsViewsPortalRosterMapping, StudentsViewsPortalVerificationSignature, StudentsViewsPortalNotificationRule,
    StudentsViewsPortalAnalyticalSnapshot, StudentsViewsPortalComplianceLog, StudentsViewsPortalIntegrationBridge,
    StudentsViewsPortalSecurityPermit, StudentsViewsPortalDocumentAttachment, StudentsViewsPortalLifecycleTransition
)

@admin.register(StudentsViewsPortalMaster)
class StudentsViewsPortalMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsViewsPortalConfiguration)
class StudentsViewsPortalConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsViewsPortalAuditTransaction)
class StudentsViewsPortalAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsViewsPortalLedger)
class StudentsViewsPortalLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsViewsPortalScheduleMatrix)
class StudentsViewsPortalScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsViewsPortalEvaluationMetric)
class StudentsViewsPortalEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsViewsPortalComplianceLog)
class StudentsViewsPortalComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
