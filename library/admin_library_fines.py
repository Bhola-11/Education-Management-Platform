"""
Django Admin Configuration for Library: Library Overdue Fines
"""

from django.contrib import admin
from library.models_library_fines import (
    LibraryFinesMaster, LibraryFinesConfiguration, LibraryFinesLedger,
    LibraryFinesAuditTransaction, LibraryFinesScheduleMatrix, LibraryFinesEvaluationMetric,
    LibraryFinesRosterMapping, LibraryFinesVerificationSignature, LibraryFinesNotificationRule,
    LibraryFinesAnalyticalSnapshot, LibraryFinesComplianceLog, LibraryFinesIntegrationBridge,
    LibraryFinesSecurityPermit, LibraryFinesDocumentAttachment, LibraryFinesLifecycleTransition
)

@admin.register(LibraryFinesMaster)
class LibraryFinesMasterAdmin(admin.ModelAdmin):
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

@admin.register(LibraryFinesConfiguration)
class LibraryFinesConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(LibraryFinesAuditTransaction)
class LibraryFinesAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(LibraryFinesLedger)
class LibraryFinesLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(LibraryFinesScheduleMatrix)
class LibraryFinesScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(LibraryFinesEvaluationMetric)
class LibraryFinesEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(LibraryFinesComplianceLog)
class LibraryFinesComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
