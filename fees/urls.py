"""
URL Routes for Fees: Payment Processing
"""

from django.urls import path
from fees import views_fees_payments as views

app_name = "fees"

urlpatterns = [
    path("fees_payments/", views.FeesPaymentsListView.as_view(), name="fees_payments_list"),
    path("fees_payments/<int:pk>/", views.FeesPaymentsDetailView.as_view(), name="fees_payments_detail"),
    path("fees_payments/create/", views.FeesPaymentsCreateView.as_view(), name="fees_payments_create"),
    path("fees_payments/<int:pk>/edit/", views.FeesPaymentsUpdateView.as_view(), name="fees_payments_update"),
    path("fees_payments/<int:pk>/delete/", views.FeesPaymentsDeleteView.as_view(), name="fees_payments_delete"),
    path("fees_payments/<int:pk>/print/", views.FeesPaymentsPrintView.as_view(), name="fees_payments_print"),
    path("fees_payments/analytics/", views.FeesPaymentsAnalyticsView.as_view(), name="fees_payments_analytics"),
    path("fees_payments/export/csv/", views.export_fees_payments_csv, name="fees_payments_export_csv"),
    path("fees_payments/export/json/", views.export_fees_payments_json, name="fees_payments_export_json"),
]
