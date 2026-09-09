"""
Django Admin Configuration for Enrollment: Prerequisite Enforcement
"""

from django.contrib import admin
from enrollment.models_enrollment_prereq_check import (
    EnrollmentPrereqCheckMaster, EnrollmentPrereqCheckConfiguration, EnrollmentPrereqCheckLedger,
    EnrollmentPrereqCheckAuditTransaction, EnrollmentPrereqCheckScheduleMatrix, EnrollmentPrereqCheckEvaluationMetric,
    EnrollmentPrereqCheckRosterMapping, EnrollmentPrereqCheckVerificationSignature, EnrollmentPrereqCheckNotificationRule,
    EnrollmentPrereqCheckAnalyticalSnapshot, EnrollmentPrereqCheckComplianceLog, EnrollmentPrereqCheckIntegrationBridge,
    EnrollmentPrereqCheckSecurityPermit, EnrollmentPrereqCheckDocumentAttachment, EnrollmentPrereqCheckLifecycleTransition
)

@admin.register(EnrollmentPrereqCheckMaster)
class EnrollmentPrereqCheckMasterAdmin(admin.ModelAdmin):
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

@admin.register(EnrollmentPrereqCheckConfiguration)
class EnrollmentPrereqCheckConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(EnrollmentPrereqCheckAuditTransaction)
class EnrollmentPrereqCheckAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(EnrollmentPrereqCheckLedger)
class EnrollmentPrereqCheckLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(EnrollmentPrereqCheckScheduleMatrix)
class EnrollmentPrereqCheckScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(EnrollmentPrereqCheckEvaluationMetric)
class EnrollmentPrereqCheckEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(EnrollmentPrereqCheckComplianceLog)
class EnrollmentPrereqCheckComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
