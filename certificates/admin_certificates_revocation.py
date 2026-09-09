"""
Django Admin Configuration for Certificates: Certificate Revocation Registry
"""

from django.contrib import admin
from certificates.models_certificates_revocation import (
    CertificatesRevocationMaster, CertificatesRevocationConfiguration, CertificatesRevocationLedger,
    CertificatesRevocationAuditTransaction, CertificatesRevocationScheduleMatrix, CertificatesRevocationEvaluationMetric,
    CertificatesRevocationRosterMapping, CertificatesRevocationVerificationSignature, CertificatesRevocationNotificationRule,
    CertificatesRevocationAnalyticalSnapshot, CertificatesRevocationComplianceLog, CertificatesRevocationIntegrationBridge,
    CertificatesRevocationSecurityPermit, CertificatesRevocationDocumentAttachment, CertificatesRevocationLifecycleTransition
)

@admin.register(CertificatesRevocationMaster)
class CertificatesRevocationMasterAdmin(admin.ModelAdmin):
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

@admin.register(CertificatesRevocationConfiguration)
class CertificatesRevocationConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CertificatesRevocationAuditTransaction)
class CertificatesRevocationAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CertificatesRevocationLedger)
class CertificatesRevocationLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CertificatesRevocationScheduleMatrix)
class CertificatesRevocationScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CertificatesRevocationEvaluationMetric)
class CertificatesRevocationEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CertificatesRevocationComplianceLog)
class CertificatesRevocationComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
