"""
Django Admin Configuration for Students: Student Lifecycle
"""

from django.contrib import admin
from students.models_students_lifecycle import (
    StudentsLifecycleMaster, StudentsLifecycleConfiguration, StudentsLifecycleLedger,
    StudentsLifecycleAuditTransaction, StudentsLifecycleScheduleMatrix, StudentsLifecycleEvaluationMetric,
    StudentsLifecycleRosterMapping, StudentsLifecycleVerificationSignature, StudentsLifecycleNotificationRule,
    StudentsLifecycleAnalyticalSnapshot, StudentsLifecycleComplianceLog, StudentsLifecycleIntegrationBridge,
    StudentsLifecycleSecurityPermit, StudentsLifecycleDocumentAttachment, StudentsLifecycleLifecycleTransition
)

@admin.register(StudentsLifecycleMaster)
class StudentsLifecycleMasterAdmin(admin.ModelAdmin):
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

@admin.register(StudentsLifecycleConfiguration)
class StudentsLifecycleConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(StudentsLifecycleAuditTransaction)
class StudentsLifecycleAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(StudentsLifecycleLedger)
class StudentsLifecycleLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(StudentsLifecycleScheduleMatrix)
class StudentsLifecycleScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(StudentsLifecycleEvaluationMetric)
class StudentsLifecycleEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(StudentsLifecycleComplianceLog)
class StudentsLifecycleComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
