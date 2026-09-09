"""
Django Admin Configuration for Core: Production Readiness
"""

from django.contrib import admin
from core.models_production_readiness import (
    ProductionReadinessMaster, ProductionReadinessConfiguration, ProductionReadinessLedger,
    ProductionReadinessAuditTransaction, ProductionReadinessScheduleMatrix, ProductionReadinessEvaluationMetric,
    ProductionReadinessRosterMapping, ProductionReadinessVerificationSignature, ProductionReadinessNotificationRule,
    ProductionReadinessAnalyticalSnapshot, ProductionReadinessComplianceLog, ProductionReadinessIntegrationBridge,
    ProductionReadinessSecurityPermit, ProductionReadinessDocumentAttachment, ProductionReadinessLifecycleTransition
)

@admin.register(ProductionReadinessMaster)
class ProductionReadinessMasterAdmin(admin.ModelAdmin):
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

@admin.register(ProductionReadinessConfiguration)
class ProductionReadinessConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(ProductionReadinessAuditTransaction)
class ProductionReadinessAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(ProductionReadinessLedger)
class ProductionReadinessLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(ProductionReadinessScheduleMatrix)
class ProductionReadinessScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(ProductionReadinessEvaluationMetric)
class ProductionReadinessEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(ProductionReadinessComplianceLog)
class ProductionReadinessComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
