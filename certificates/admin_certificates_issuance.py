"""
Django Admin Configuration for Certificates: Certificate Issuance Pipeline
"""

from django.contrib import admin
from certificates.models_certificates_issuance import (
    CertificatesIssuanceMaster, CertificatesIssuanceConfiguration, CertificatesIssuanceLedger,
    CertificatesIssuanceAuditTransaction, CertificatesIssuanceScheduleMatrix, CertificatesIssuanceEvaluationMetric,
    CertificatesIssuanceRosterMapping, CertificatesIssuanceVerificationSignature, CertificatesIssuanceNotificationRule,
    CertificatesIssuanceAnalyticalSnapshot, CertificatesIssuanceComplianceLog, CertificatesIssuanceIntegrationBridge,
    CertificatesIssuanceSecurityPermit, CertificatesIssuanceDocumentAttachment, CertificatesIssuanceLifecycleTransition
)

@admin.register(CertificatesIssuanceMaster)
class CertificatesIssuanceMasterAdmin(admin.ModelAdmin):
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

@admin.register(CertificatesIssuanceConfiguration)
class CertificatesIssuanceConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CertificatesIssuanceAuditTransaction)
class CertificatesIssuanceAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CertificatesIssuanceLedger)
class CertificatesIssuanceLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CertificatesIssuanceScheduleMatrix)
class CertificatesIssuanceScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CertificatesIssuanceEvaluationMetric)
class CertificatesIssuanceEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CertificatesIssuanceComplianceLog)
class CertificatesIssuanceComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
