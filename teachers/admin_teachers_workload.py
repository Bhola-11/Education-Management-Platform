"""
Django Admin Configuration for Teachers: Faculty Workload
"""

from django.contrib import admin
from teachers.models_teachers_workload import (
    TeachersWorkloadMaster, TeachersWorkloadConfiguration, TeachersWorkloadLedger,
    TeachersWorkloadAuditTransaction, TeachersWorkloadScheduleMatrix, TeachersWorkloadEvaluationMetric,
    TeachersWorkloadRosterMapping, TeachersWorkloadVerificationSignature, TeachersWorkloadNotificationRule,
    TeachersWorkloadAnalyticalSnapshot, TeachersWorkloadComplianceLog, TeachersWorkloadIntegrationBridge,
    TeachersWorkloadSecurityPermit, TeachersWorkloadDocumentAttachment, TeachersWorkloadLifecycleTransition
)

@admin.register(TeachersWorkloadMaster)
class TeachersWorkloadMasterAdmin(admin.ModelAdmin):
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

@admin.register(TeachersWorkloadConfiguration)
class TeachersWorkloadConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(TeachersWorkloadAuditTransaction)
class TeachersWorkloadAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(TeachersWorkloadLedger)
class TeachersWorkloadLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(TeachersWorkloadScheduleMatrix)
class TeachersWorkloadScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(TeachersWorkloadEvaluationMetric)
class TeachersWorkloadEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(TeachersWorkloadComplianceLog)
class TeachersWorkloadComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
