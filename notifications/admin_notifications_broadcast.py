"""
Django Admin Configuration for Notifications: Campus Broadcasts
"""

from django.contrib import admin
from notifications.models_notifications_broadcast import (
    NotificationsBroadcastMaster, NotificationsBroadcastConfiguration, NotificationsBroadcastLedger,
    NotificationsBroadcastAuditTransaction, NotificationsBroadcastScheduleMatrix, NotificationsBroadcastEvaluationMetric,
    NotificationsBroadcastRosterMapping, NotificationsBroadcastVerificationSignature, NotificationsBroadcastNotificationRule,
    NotificationsBroadcastAnalyticalSnapshot, NotificationsBroadcastComplianceLog, NotificationsBroadcastIntegrationBridge,
    NotificationsBroadcastSecurityPermit, NotificationsBroadcastDocumentAttachment, NotificationsBroadcastLifecycleTransition
)

@admin.register(NotificationsBroadcastMaster)
class NotificationsBroadcastMasterAdmin(admin.ModelAdmin):
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

@admin.register(NotificationsBroadcastConfiguration)
class NotificationsBroadcastConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(NotificationsBroadcastAuditTransaction)
class NotificationsBroadcastAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(NotificationsBroadcastLedger)
class NotificationsBroadcastLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(NotificationsBroadcastScheduleMatrix)
class NotificationsBroadcastScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(NotificationsBroadcastEvaluationMetric)
class NotificationsBroadcastEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(NotificationsBroadcastComplianceLog)
class NotificationsBroadcastComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
