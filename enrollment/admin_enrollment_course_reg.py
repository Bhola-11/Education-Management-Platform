"""
Django Admin Configuration for Enrollment: Course Registration
"""

from django.contrib import admin
from enrollment.models_enrollment_course_reg import (
    EnrollmentCourseRegMaster, EnrollmentCourseRegConfiguration, EnrollmentCourseRegLedger,
    EnrollmentCourseRegAuditTransaction, EnrollmentCourseRegScheduleMatrix, EnrollmentCourseRegEvaluationMetric,
    EnrollmentCourseRegRosterMapping, EnrollmentCourseRegVerificationSignature, EnrollmentCourseRegNotificationRule,
    EnrollmentCourseRegAnalyticalSnapshot, EnrollmentCourseRegComplianceLog, EnrollmentCourseRegIntegrationBridge,
    EnrollmentCourseRegSecurityPermit, EnrollmentCourseRegDocumentAttachment, EnrollmentCourseRegLifecycleTransition
)

@admin.register(EnrollmentCourseRegMaster)
class EnrollmentCourseRegMasterAdmin(admin.ModelAdmin):
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

@admin.register(EnrollmentCourseRegConfiguration)
class EnrollmentCourseRegConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(EnrollmentCourseRegAuditTransaction)
class EnrollmentCourseRegAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(EnrollmentCourseRegLedger)
class EnrollmentCourseRegLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(EnrollmentCourseRegScheduleMatrix)
class EnrollmentCourseRegScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(EnrollmentCourseRegEvaluationMetric)
class EnrollmentCourseRegEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(EnrollmentCourseRegComplianceLog)
class EnrollmentCourseRegComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
