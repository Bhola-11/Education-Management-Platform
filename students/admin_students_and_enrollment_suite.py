"""
Django Admin Configuration for Students: Students & Enrollment Tests
"""

from django.contrib import admin
from students.models_students_and_enrollment_suite import (
    StudentsAndEnrollmentSuiteMaster, StudentsAndEnrollmentSuiteConfiguration, StudentsAndEnrollmentSuiteLedger,
    StudentsAndEnrollmentSuiteAuditTransaction, StudentsAndEnrollmentSuiteScheduleMatrix, StudentsAndEnrollmentSuiteEvaluationMetric,
    StudentsAndEnrollmentSuiteRosterMapping, StudentsAndEnrollmentSuiteVerificationSignature, StudentsAndEnrollmentSuiteNotificationRule,
    StudentsAndEnrollmentSuiteAnalyticalSnapshot, StudentsAndEnrollmentSuiteComplianceLog, StudentsAndEnrollmentSuiteIntegrationBridge,
    StudentsAndEnrollmentSuiteSecurityPermit, StudentsAndEnrollmentSuiteDocumentAttachment, StudentsAndEnrollmentSuiteLifecycleTransition
)

@admin.register(StudentsAndEnrollmentSuiteMaster)
class StudentsAndEnrollmentSuiteMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsAndEnrollmentSuiteConfiguration)
class StudentsAndEnrollmentSuiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsAndEnrollmentSuiteAuditTransaction)
class StudentsAndEnrollmentSuiteAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsAndEnrollmentSuiteLedger)
class StudentsAndEnrollmentSuiteLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsAndEnrollmentSuiteScheduleMatrix)
class StudentsAndEnrollmentSuiteScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsAndEnrollmentSuiteEvaluationMetric)
class StudentsAndEnrollmentSuiteEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsAndEnrollmentSuiteComplianceLog)
class StudentsAndEnrollmentSuiteComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
