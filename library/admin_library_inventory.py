"""
Django Admin Configuration for Library: Physical Inventory
"""

from django.contrib import admin
from library.models_library_inventory import (
    LibraryInventoryMaster, LibraryInventoryConfiguration, LibraryInventoryLedger,
    LibraryInventoryAuditTransaction, LibraryInventoryScheduleMatrix, LibraryInventoryEvaluationMetric,
    LibraryInventoryRosterMapping, LibraryInventoryVerificationSignature, LibraryInventoryNotificationRule,
    LibraryInventoryAnalyticalSnapshot, LibraryInventoryComplianceLog, LibraryInventoryIntegrationBridge,
    LibraryInventorySecurityPermit, LibraryInventoryDocumentAttachment, LibraryInventoryLifecycleTransition
)

@admin.register(LibraryInventoryMaster)
class LibraryInventoryMasterAdmin(admin.ModelAdmin):
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

@admin.register(LibraryInventoryConfiguration)
class LibraryInventoryConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(LibraryInventoryAuditTransaction)
class LibraryInventoryAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(LibraryInventoryLedger)
class LibraryInventoryLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(LibraryInventoryScheduleMatrix)
class LibraryInventoryScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(LibraryInventoryEvaluationMetric)
class LibraryInventoryEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(LibraryInventoryComplianceLog)
class LibraryInventoryComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
