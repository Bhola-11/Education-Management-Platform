"""
URL Routes for Core: Security Audit Trail
"""

from django.urls import path
from core import views_core_audit_logging as views

app_name = "core"

urlpatterns = [
    path("core_audit_logging/", views.CoreAuditLoggingListView.as_view(), name="core_audit_logging_list"),
    path("core_audit_logging/<int:pk>/", views.CoreAuditLoggingDetailView.as_view(), name="core_audit_logging_detail"),
    path("core_audit_logging/create/", views.CoreAuditLoggingCreateView.as_view(), name="core_audit_logging_create"),
    path("core_audit_logging/<int:pk>/edit/", views.CoreAuditLoggingUpdateView.as_view(), name="core_audit_logging_update"),
    path("core_audit_logging/<int:pk>/delete/", views.CoreAuditLoggingDeleteView.as_view(), name="core_audit_logging_delete"),
    path("core_audit_logging/<int:pk>/print/", views.CoreAuditLoggingPrintView.as_view(), name="core_audit_logging_print"),
    path("core_audit_logging/analytics/", views.CoreAuditLoggingAnalyticsView.as_view(), name="core_audit_logging_analytics"),
    path("core_audit_logging/export/csv/", views.export_core_audit_logging_csv, name="core_audit_logging_export_csv"),
    path("core_audit_logging/export/json/", views.export_core_audit_logging_json, name="core_audit_logging_export_json"),
]
