"""
URL Routes for Fees: Student Fee Invoicing
"""

from django.urls import path
from fees import views_fees_invoicing as views

app_name = "fees"

urlpatterns = [
    path("fees_invoicing/", views.FeesInvoicingListView.as_view(), name="fees_invoicing_list"),
    path("fees_invoicing/<int:pk>/", views.FeesInvoicingDetailView.as_view(), name="fees_invoicing_detail"),
    path("fees_invoicing/create/", views.FeesInvoicingCreateView.as_view(), name="fees_invoicing_create"),
    path("fees_invoicing/<int:pk>/edit/", views.FeesInvoicingUpdateView.as_view(), name="fees_invoicing_update"),
    path("fees_invoicing/<int:pk>/delete/", views.FeesInvoicingDeleteView.as_view(), name="fees_invoicing_delete"),
    path("fees_invoicing/<int:pk>/print/", views.FeesInvoicingPrintView.as_view(), name="fees_invoicing_print"),
    path("fees_invoicing/analytics/", views.FeesInvoicingAnalyticsView.as_view(), name="fees_invoicing_analytics"),
    path("fees_invoicing/export/csv/", views.export_fees_invoicing_csv, name="fees_invoicing_export_csv"),
    path("fees_invoicing/export/json/", views.export_fees_invoicing_json, name="fees_invoicing_export_json"),
]
