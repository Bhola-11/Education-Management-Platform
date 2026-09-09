"""
URL Routes for Fees: Installment Plans
"""

from django.urls import path
from fees import views_fees_installments as views

app_name = "fees"

urlpatterns = [
    path("fees_installments/", views.FeesInstallmentsListView.as_view(), name="fees_installments_list"),
    path("fees_installments/<int:pk>/", views.FeesInstallmentsDetailView.as_view(), name="fees_installments_detail"),
    path("fees_installments/create/", views.FeesInstallmentsCreateView.as_view(), name="fees_installments_create"),
    path("fees_installments/<int:pk>/edit/", views.FeesInstallmentsUpdateView.as_view(), name="fees_installments_update"),
    path("fees_installments/<int:pk>/delete/", views.FeesInstallmentsDeleteView.as_view(), name="fees_installments_delete"),
    path("fees_installments/<int:pk>/print/", views.FeesInstallmentsPrintView.as_view(), name="fees_installments_print"),
    path("fees_installments/analytics/", views.FeesInstallmentsAnalyticsView.as_view(), name="fees_installments_analytics"),
    path("fees_installments/export/csv/", views.export_fees_installments_csv, name="fees_installments_export_csv"),
    path("fees_installments/export/json/", views.export_fees_installments_json, name="fees_installments_export_json"),
]
