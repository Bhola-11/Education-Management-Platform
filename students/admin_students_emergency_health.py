"""
Django Admin Configuration for Students: Student Health & Safety
"""

from django.contrib import admin
from students.models_students_emergency_health import (
    StudentsEmergencyHealthMaster, StudentsEmergencyHealthConfiguration, StudentsEmergencyHealthLedger,
    StudentsEmergencyHealthAuditTransaction, StudentsEmergencyHealthScheduleMatrix, StudentsEmergencyHealthEvaluationMetric,
    StudentsEmergencyHealthRosterMapping, StudentsEmergencyHealthVerificationSignature, StudentsEmergencyHealthNotificationRule,
    StudentsEmergencyHealthAnalyticalSnapshot, StudentsEmergencyHealthComplianceLog, StudentsEmergencyHealthIntegrationBridge,
    StudentsEmergencyHealthSecurityPermit, StudentsEmergencyHealthDocumentAttachment, StudentsEmergencyHealthLifecycleTransition
)

@admin.register(StudentsEmergencyHealthMaster)
class StudentsEmergencyHealthMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsEmergencyHealthConfiguration)
class StudentsEmergencyHealthConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsEmergencyHealthAuditTransaction)
class StudentsEmergencyHealthAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsEmergencyHealthLedger)
class StudentsEmergencyHealthLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsEmergencyHealthScheduleMatrix)
class StudentsEmergencyHealthScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsEmergencyHealthEvaluationMetric)
class StudentsEmergencyHealthEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsEmergencyHealthComplianceLog)
class StudentsEmergencyHealthComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
