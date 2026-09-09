"""
Django Admin Configuration for Students: Student Master Record
"""

from django.contrib import admin
from students.models_students_master_record import (
    StudentsMasterRecordMaster, StudentsMasterRecordConfiguration, StudentsMasterRecordLedger,
    StudentsMasterRecordAuditTransaction, StudentsMasterRecordScheduleMatrix, StudentsMasterRecordEvaluationMetric,
    StudentsMasterRecordRosterMapping, StudentsMasterRecordVerificationSignature, StudentsMasterRecordNotificationRule,
    StudentsMasterRecordAnalyticalSnapshot, StudentsMasterRecordComplianceLog, StudentsMasterRecordIntegrationBridge,
    StudentsMasterRecordSecurityPermit, StudentsMasterRecordDocumentAttachment, StudentsMasterRecordLifecycleTransition
)

@admin.register(StudentsMasterRecordMaster)
class StudentsMasterRecordMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsMasterRecordConfiguration)
class StudentsMasterRecordConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsMasterRecordAuditTransaction)
class StudentsMasterRecordAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsMasterRecordLedger)
class StudentsMasterRecordLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsMasterRecordScheduleMatrix)
class StudentsMasterRecordScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsMasterRecordEvaluationMetric)
class StudentsMasterRecordEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsMasterRecordComplianceLog)
class StudentsMasterRecordComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
