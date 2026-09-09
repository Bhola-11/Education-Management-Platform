"""
Django Admin Configuration for Academics: Course Catalog
"""

from django.contrib import admin
from academics.models_academics_courses import (
    AcademicsCoursesMaster, AcademicsCoursesConfiguration, AcademicsCoursesLedger,
    AcademicsCoursesAuditTransaction, AcademicsCoursesScheduleMatrix, AcademicsCoursesEvaluationMetric,
    AcademicsCoursesRosterMapping, AcademicsCoursesVerificationSignature, AcademicsCoursesNotificationRule,
    AcademicsCoursesAnalyticalSnapshot, AcademicsCoursesComplianceLog, AcademicsCoursesIntegrationBridge,
    AcademicsCoursesSecurityPermit, AcademicsCoursesDocumentAttachment, AcademicsCoursesLifecycleTransition
)

@admin.register(AcademicsCoursesMaster)
class AcademicsCoursesMasterAdmin(admin.ModelAdmin):
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

@admin.register(AcademicsCoursesConfiguration)
class AcademicsCoursesConfigurationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "priority", "status", "created_at")
    search_fields = ("code", "name")

@admin.register(AcademicsCoursesAuditTransaction)
class AcademicsCoursesAuditTransactionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

@admin.register(AcademicsCoursesLedger)
class AcademicsCoursesLedgerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monetary_value", "status")

@admin.register(AcademicsCoursesScheduleMatrix)
class AcademicsCoursesScheduleMatrixAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "effective_date")

@admin.register(AcademicsCoursesEvaluationMetric)
class AcademicsCoursesEvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "score_rating", "is_active")

@admin.register(AcademicsCoursesComplianceLog)
class AcademicsCoursesComplianceLogAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_verified", "created_at")
