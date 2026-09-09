"""
Django Admin Configuration for Enrollment: Application Decisioning
"""

from django.contrib import admin
from enrollment.models_enrollment_review import (
    EnrollmentReviewMaster, EnrollmentReviewConfiguration, EnrollmentReviewLedger,
    EnrollmentReviewAuditTransaction, EnrollmentReviewScheduleMatrix, EnrollmentReviewEvaluationMetric,
    EnrollmentReviewRosterMapping, EnrollmentReviewVerificationSignature, EnrollmentReviewNotificationRule,
    EnrollmentReviewAnalyticalSnapshot, EnrollmentReviewComplianceLog, EnrollmentReviewIntegrationBridge,
    EnrollmentReviewSecurityPermit, EnrollmentReviewDocumentAttachment, EnrollmentReviewLifecycleTransition
)

@admin.register(EnrollmentReviewMaster)
class EnrollmentReviewMasterAdmin(admin.ModelAdmin):
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

@admin.register(EnrollmentReviewConfiguration)
class EnrollmentReviewConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(EnrollmentReviewAuditTransaction)
class EnrollmentReviewAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(EnrollmentReviewLedger)
class EnrollmentReviewLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(EnrollmentReviewScheduleMatrix)
class EnrollmentReviewScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(EnrollmentReviewEvaluationMetric)
class EnrollmentReviewEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(EnrollmentReviewComplianceLog)
class EnrollmentReviewComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
