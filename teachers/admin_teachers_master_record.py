"""
Django Admin Configuration for Teachers: Faculty Master Record
"""

from django.contrib import admin
from teachers.models_teachers_master_record import (
    TeachersMasterRecordMaster, TeachersMasterRecordConfiguration, TeachersMasterRecordLedger,
    TeachersMasterRecordAuditTransaction, TeachersMasterRecordScheduleMatrix, TeachersMasterRecordEvaluationMetric,
    TeachersMasterRecordRosterMapping, TeachersMasterRecordVerificationSignature, TeachersMasterRecordNotificationRule,
    TeachersMasterRecordAnalyticalSnapshot, TeachersMasterRecordComplianceLog, TeachersMasterRecordIntegrationBridge,
    TeachersMasterRecordSecurityPermit, TeachersMasterRecordDocumentAttachment, TeachersMasterRecordLifecycleTransition
)

@admin.register(TeachersMasterRecordMaster)
class TeachersMasterRecordMasterAdmin(admin.ModelAdmin):
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

@admin.register(TeachersMasterRecordConfiguration)
class TeachersMasterRecordConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(TeachersMasterRecordAuditTransaction)
class TeachersMasterRecordAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(TeachersMasterRecordLedger)
class TeachersMasterRecordLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(TeachersMasterRecordScheduleMatrix)
class TeachersMasterRecordScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(TeachersMasterRecordEvaluationMetric)
class TeachersMasterRecordEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(TeachersMasterRecordComplianceLog)
class TeachersMasterRecordComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
