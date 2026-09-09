"""
Django Admin Configuration for Enrollment: Cohorts & Sections
"""

from django.contrib import admin
from enrollment.models_enrollment_cohorts import (
    EnrollmentCohortsMaster, EnrollmentCohortsConfiguration, EnrollmentCohortsLedger,
    EnrollmentCohortsAuditTransaction, EnrollmentCohortsScheduleMatrix, EnrollmentCohortsEvaluationMetric,
    EnrollmentCohortsRosterMapping, EnrollmentCohortsVerificationSignature, EnrollmentCohortsNotificationRule,
    EnrollmentCohortsAnalyticalSnapshot, EnrollmentCohortsComplianceLog, EnrollmentCohortsIntegrationBridge,
    EnrollmentCohortsSecurityPermit, EnrollmentCohortsDocumentAttachment, EnrollmentCohortsLifecycleTransition
)

@admin.register(EnrollmentCohortsMaster)
class EnrollmentCohortsMasterAdmin(admin.ModelAdmin):
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

@admin.register(EnrollmentCohortsConfiguration)
class EnrollmentCohortsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(EnrollmentCohortsAuditTransaction)
class EnrollmentCohortsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(EnrollmentCohortsLedger)
class EnrollmentCohortsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(EnrollmentCohortsScheduleMatrix)
class EnrollmentCohortsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(EnrollmentCohortsEvaluationMetric)
class EnrollmentCohortsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(EnrollmentCohortsComplianceLog)
class EnrollmentCohortsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
