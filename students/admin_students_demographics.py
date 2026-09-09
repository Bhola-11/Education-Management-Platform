"""
Django Admin Configuration for Students: Student Demographics
"""

from django.contrib import admin
from students.models_students_demographics import (
    StudentsDemographicsMaster, StudentsDemographicsConfiguration, StudentsDemographicsLedger,
    StudentsDemographicsAuditTransaction, StudentsDemographicsScheduleMatrix, StudentsDemographicsEvaluationMetric,
    StudentsDemographicsRosterMapping, StudentsDemographicsVerificationSignature, StudentsDemographicsNotificationRule,
    StudentsDemographicsAnalyticalSnapshot, StudentsDemographicsComplianceLog, StudentsDemographicsIntegrationBridge,
    StudentsDemographicsSecurityPermit, StudentsDemographicsDocumentAttachment, StudentsDemographicsLifecycleTransition
)

@admin.register(StudentsDemographicsMaster)
class StudentsDemographicsMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsDemographicsConfiguration)
class StudentsDemographicsConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsDemographicsAuditTransaction)
class StudentsDemographicsAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsDemographicsLedger)
class StudentsDemographicsLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsDemographicsScheduleMatrix)
class StudentsDemographicsScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsDemographicsEvaluationMetric)
class StudentsDemographicsEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsDemographicsComplianceLog)
class StudentsDemographicsComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
