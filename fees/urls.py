"""
URL Routes for Fees: Fee Ledger & Accounting
"""

from django.urls import path
from fees import views_fees_reconciliation as views

app_name = "fees"

urlpatterns = [
    path("fees_reconciliation/", views.FeesReconciliationListView.as_view(), name="fees_reconciliation_list"),
    path("fees_reconciliation/<int:pk>/", views.FeesReconciliationDetailView.as_view(), name="fees_reconciliation_detail"),
    path("fees_reconciliation/create/", views.FeesReconciliationCreateView.as_view(), name="fees_reconciliation_create"),
    path("fees_reconciliation/<int:pk>/edit/", views.FeesReconciliationUpdateView.as_view(), name="fees_reconciliation_update"),
    path("fees_reconciliation/<int:pk>/delete/", views.FeesReconciliationDeleteView.as_view(), name="fees_reconciliation_delete"),
    path("fees_reconciliation/<int:pk>/print/", views.FeesReconciliationPrintView.as_view(), name="fees_reconciliation_print"),
    path("fees_reconciliation/analytics/", views.FeesReconciliationAnalyticsView.as_view(), name="fees_reconciliation_analytics"),
    path("fees_reconciliation/export/csv/", views.export_fees_reconciliation_csv, name="fees_reconciliation_export_csv"),
    path("fees_reconciliation/export/json/", views.export_fees_reconciliation_json, name="fees_reconciliation_export_json"),
]
