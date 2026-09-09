"""
URL Routes for Certificates: Certificate Issuance Pipeline
"""

from django.urls import path
from certificates import views_certificates_issuance as views

app_name = "certificates"

urlpatterns = [
    path("certificates_issuance/", views.CertificatesIssuanceListView.as_view(), name="certificates_issuance_list"),
    path("certificates_issuance/<int:pk>/", views.CertificatesIssuanceDetailView.as_view(), name="certificates_issuance_detail"),
    path("certificates_issuance/create/", views.CertificatesIssuanceCreateView.as_view(), name="certificates_issuance_create"),
    path("certificates_issuance/<int:pk>/edit/", views.CertificatesIssuanceUpdateView.as_view(), name="certificates_issuance_update"),
    path("certificates_issuance/<int:pk>/delete/", views.CertificatesIssuanceDeleteView.as_view(), name="certificates_issuance_delete"),
    path("certificates_issuance/<int:pk>/print/", views.CertificatesIssuancePrintView.as_view(), name="certificates_issuance_print"),
    path("certificates_issuance/analytics/", views.CertificatesIssuanceAnalyticsView.as_view(), name="certificates_issuance_analytics"),
    path("certificates_issuance/export/csv/", views.export_certificates_issuance_csv, name="certificates_issuance_export_csv"),
    path("certificates_issuance/export/json/", views.export_certificates_issuance_json, name="certificates_issuance_export_json"),
]
