"""
Django Admin Configuration for Notifications: Notification Preferences
"""

from django.contrib import admin
from notifications.models_notifications_preferences import (
    NotificationsPreferencesMaster, NotificationsPreferencesConfiguration, NotificationsPreferencesLedger,
    NotificationsPreferencesAuditTransaction, NotificationsPreferencesScheduleMatrix, NotificationsPreferencesEvaluationMetric,
    NotificationsPreferencesRosterMapping, NotificationsPreferencesVerificationSignature, NotificationsPreferencesNotificationRule,
    NotificationsPreferencesAnalyticalSnapshot, NotificationsPreferencesComplianceLog, NotificationsPreferencesIntegrationBridge,
    NotificationsPreferencesSecurityPermit, NotificationsPreferencesDocumentAttachment, NotificationsPreferencesLifecycleTransition
)

@admin.register(NotificationsPreferencesMaster)
class NotificationsPreferencesMasterAdmin(admin.ModelAdmin):
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

@admin.register(NotificationsPreferencesConfiguration)
class NotificationsPreferencesConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(NotificationsPreferencesAuditTransaction)
class NotificationsPreferencesAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(NotificationsPreferencesLedger)
class NotificationsPreferencesLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(NotificationsPreferencesScheduleMatrix)
class NotificationsPreferencesScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(NotificationsPreferencesEvaluationMetric)
class NotificationsPreferencesEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(NotificationsPreferencesComplianceLog)
class NotificationsPreferencesComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
