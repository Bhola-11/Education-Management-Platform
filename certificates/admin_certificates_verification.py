"""
Django Admin Configuration for Certificates: Cryptographic Verification
"""

from django.contrib import admin
from certificates.models_certificates_verification import (
    CertificatesVerificationMaster, CertificatesVerificationConfiguration, CertificatesVerificationLedger,
    CertificatesVerificationAuditTransaction, CertificatesVerificationScheduleMatrix, CertificatesVerificationEvaluationMetric,
    CertificatesVerificationRosterMapping, CertificatesVerificationVerificationSignature, CertificatesVerificationNotificationRule,
    CertificatesVerificationAnalyticalSnapshot, CertificatesVerificationComplianceLog, CertificatesVerificationIntegrationBridge,
    CertificatesVerificationSecurityPermit, CertificatesVerificationDocumentAttachment, CertificatesVerificationLifecycleTransition
)

@admin.register(CertificatesVerificationMaster)
class CertificatesVerificationMasterAdmin(admin.ModelAdmin):
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

@admin.register(CertificatesVerificationConfiguration)
class CertificatesVerificationConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(CertificatesVerificationAuditTransaction)
class CertificatesVerificationAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(CertificatesVerificationLedger)
class CertificatesVerificationLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(CertificatesVerificationScheduleMatrix)
class CertificatesVerificationScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(CertificatesVerificationEvaluationMetric)
class CertificatesVerificationEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(CertificatesVerificationComplianceLog)
class CertificatesVerificationComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
