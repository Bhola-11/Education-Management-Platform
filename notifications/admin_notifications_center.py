"""
Django Admin Configuration for Notifications: Notification Center
"""

from django.contrib import admin
from notifications.models_notifications_center import (
    NotificationsCenterMaster, NotificationsCenterConfiguration, NotificationsCenterLedger,
    NotificationsCenterAuditTransaction, NotificationsCenterScheduleMatrix, NotificationsCenterEvaluationMetric,
    NotificationsCenterRosterMapping, NotificationsCenterVerificationSignature, NotificationsCenterNotificationRule,
    NotificationsCenterAnalyticalSnapshot, NotificationsCenterComplianceLog, NotificationsCenterIntegrationBridge,
    NotificationsCenterSecurityPermit, NotificationsCenterDocumentAttachment, NotificationsCenterLifecycleTransition
)

@admin.register(NotificationsCenterMaster)
class NotificationsCenterMasterAdmin(admin.ModelAdmin):
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

@admin.register(NotificationsCenterConfiguration)
class NotificationsCenterConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(NotificationsCenterAuditTransaction)
class NotificationsCenterAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(NotificationsCenterLedger)
class NotificationsCenterLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(NotificationsCenterScheduleMatrix)
class NotificationsCenterScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(NotificationsCenterEvaluationMetric)
class NotificationsCenterEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(NotificationsCenterComplianceLog)
class NotificationsCenterComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
