"""
Django Admin Configuration for Enrollment: Admissions Pipeline
"""

from django.contrib import admin
from enrollment.models_enrollment_admissions import (
    EnrollmentAdmissionsMaster, EnrollmentAdmissionsConfiguration, EnrollmentAdmissionsLedger,
    EnrollmentAdmissionsAuditTransaction, EnrollmentAdmissionsScheduleMatrix, EnrollmentAdmissionsEvaluationMetric,
    EnrollmentAdmissionsRosterMapping, EnrollmentAdmissionsVerificationSignature, EnrollmentAdmissionsNotificationRule,
    EnrollmentAdmissionsAnalyticalSnapshot, EnrollmentAdmissionsComplianceLog, EnrollmentAdmissionsIntegrationBridge,
    EnrollmentAdmissionsSecurityPermit, EnrollmentAdmissionsDocumentAttachment, EnrollmentAdmissionsLifecycleTransition
)

@admin.register(EnrollmentAdmissionsMaster)
class EnrollmentAdmissionsMasterAdmin(admin.ModelAdmin):
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

@admin.register(EnrollmentAdmissionsConfiguration)
class EnrollmentAdmissionsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(EnrollmentAdmissionsAuditTransaction)
class EnrollmentAdmissionsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(EnrollmentAdmissionsLedger)
class EnrollmentAdmissionsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(EnrollmentAdmissionsScheduleMatrix)
class EnrollmentAdmissionsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(EnrollmentAdmissionsEvaluationMetric)
class EnrollmentAdmissionsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(EnrollmentAdmissionsComplianceLog)
class EnrollmentAdmissionsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
