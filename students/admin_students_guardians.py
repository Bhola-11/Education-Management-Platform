"""
Django Admin Configuration for Students: Guardians & Parents
"""

from django.contrib import admin
from students.models_students_guardians import (
    StudentsGuardiansMaster, StudentsGuardiansConfiguration, StudentsGuardiansLedger,
    StudentsGuardiansAuditTransaction, StudentsGuardiansScheduleMatrix, StudentsGuardiansEvaluationMetric,
    StudentsGuardiansRosterMapping, StudentsGuardiansVerificationSignature, StudentsGuardiansNotificationRule,
    StudentsGuardiansAnalyticalSnapshot, StudentsGuardiansComplianceLog, StudentsGuardiansIntegrationBridge,
    StudentsGuardiansSecurityPermit, StudentsGuardiansDocumentAttachment, StudentsGuardiansLifecycleTransition
)

@admin.register(StudentsGuardiansMaster)
class StudentsGuardiansMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsGuardiansConfiguration)
class StudentsGuardiansConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsGuardiansAuditTransaction)
class StudentsGuardiansAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsGuardiansLedger)
class StudentsGuardiansLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsGuardiansScheduleMatrix)
class StudentsGuardiansScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsGuardiansEvaluationMetric)
class StudentsGuardiansEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsGuardiansComplianceLog)
class StudentsGuardiansComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
