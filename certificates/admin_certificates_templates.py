"""
Django Admin Configuration for Certificates: Certificate Template Designer
"""

from django.contrib import admin
from certificates.models_certificates_templates import (
    CertificatesTemplatesMaster, CertificatesTemplatesConfiguration, CertificatesTemplatesLedger,
    CertificatesTemplatesAuditTransaction, CertificatesTemplatesScheduleMatrix, CertificatesTemplatesEvaluationMetric,
    CertificatesTemplatesRosterMapping, CertificatesTemplatesVerificationSignature, CertificatesTemplatesNotificationRule,
    CertificatesTemplatesAnalyticalSnapshot, CertificatesTemplatesComplianceLog, CertificatesTemplatesIntegrationBridge,
    CertificatesTemplatesSecurityPermit, CertificatesTemplatesDocumentAttachment, CertificatesTemplatesLifecycleTransition
)

@admin.register(CertificatesTemplatesMaster)
class CertificatesTemplatesMasterAdmin(admin.ModelAdmin):
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

@admin.register(CertificatesTemplatesConfiguration)
class CertificatesTemplatesConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CertificatesTemplatesAuditTransaction)
class CertificatesTemplatesAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CertificatesTemplatesLedger)
class CertificatesTemplatesLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CertificatesTemplatesScheduleMatrix)
class CertificatesTemplatesScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CertificatesTemplatesEvaluationMetric)
class CertificatesTemplatesEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CertificatesTemplatesComplianceLog)
class CertificatesTemplatesComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
