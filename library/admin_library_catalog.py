"""
Django Admin Configuration for Library: Library Cataloging
"""

from django.contrib import admin
from library.models_library_catalog import (
    LibraryCatalogMaster, LibraryCatalogConfiguration, LibraryCatalogLedger,
    LibraryCatalogAuditTransaction, LibraryCatalogScheduleMatrix, LibraryCatalogEvaluationMetric,
    LibraryCatalogRosterMapping, LibraryCatalogVerificationSignature, LibraryCatalogNotificationRule,
    LibraryCatalogAnalyticalSnapshot, LibraryCatalogComplianceLog, LibraryCatalogIntegrationBridge,
    LibraryCatalogSecurityPermit, LibraryCatalogDocumentAttachment, LibraryCatalogLifecycleTransition
)

@admin.register(LibraryCatalogMaster)
class LibraryCatalogMasterAdmin(admin.ModelAdmin):
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

@admin.register(LibraryCatalogConfiguration)
class LibraryCatalogConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(LibraryCatalogAuditTransaction)
class LibraryCatalogAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(LibraryCatalogLedger)
class LibraryCatalogLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(LibraryCatalogScheduleMatrix)
class LibraryCatalogScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(LibraryCatalogEvaluationMetric)
class LibraryCatalogEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(LibraryCatalogComplianceLog)
class LibraryCatalogComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
