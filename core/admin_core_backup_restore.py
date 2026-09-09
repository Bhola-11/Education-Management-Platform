"""
Django Admin Configuration for Core: Database Diagnostics & Snapshots
"""

from django.contrib import admin
from core.models_core_backup_restore import (
    CoreBackupRestoreMaster, CoreBackupRestoreConfiguration, CoreBackupRestoreLedger,
    CoreBackupRestoreAuditTransaction, CoreBackupRestoreScheduleMatrix, CoreBackupRestoreEvaluationMetric,
    CoreBackupRestoreRosterMapping, CoreBackupRestoreVerificationSignature, CoreBackupRestoreNotificationRule,
    CoreBackupRestoreAnalyticalSnapshot, CoreBackupRestoreComplianceLog, CoreBackupRestoreIntegrationBridge,
    CoreBackupRestoreSecurityPermit, CoreBackupRestoreDocumentAttachment, CoreBackupRestoreLifecycleTransition
)

@admin.register(CoreBackupRestoreMaster)
class CoreBackupRestoreMasterAdmin(admin.ModelAdmin):
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

@admin.register(CoreBackupRestoreConfiguration)
class CoreBackupRestoreConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CoreBackupRestoreAuditTransaction)
class CoreBackupRestoreAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CoreBackupRestoreLedger)
class CoreBackupRestoreLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CoreBackupRestoreScheduleMatrix)
class CoreBackupRestoreScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CoreBackupRestoreEvaluationMetric)
class CoreBackupRestoreEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CoreBackupRestoreComplianceLog)
class CoreBackupRestoreComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
