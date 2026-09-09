"""
URL Routes for Certificates: Certificate Revocation Registry
"""

from django.urls import path
from certificates import views_certificates_revocation as views

app_name = "certificates"

urlpatterns = [
    path("certificates_revocation/", views.CertificatesRevocationListView.as_view(), name="certificates_revocation_list"),
    path("certificates_revocation/<int:pk>/", views.CertificatesRevocationDetailView.as_view(), name="certificates_revocation_detail"),
    path("certificates_revocation/create/", views.CertificatesRevocationCreateView.as_view(), name="certificates_revocation_create"),
    path("certificates_revocation/<int:pk>/edit/", views.CertificatesRevocationUpdateView.as_view(), name="certificates_revocation_update"),
    path("certificates_revocation/<int:pk>/delete/", views.CertificatesRevocationDeleteView.as_view(), name="certificates_revocation_delete"),
    path("certificates_revocation/<int:pk>/print/", views.CertificatesRevocationPrintView.as_view(), name="certificates_revocation_print"),
    path("certificates_revocation/analytics/", views.CertificatesRevocationAnalyticsView.as_view(), name="certificates_revocation_analytics"),
    path("certificates_revocation/export/csv/", views.export_certificates_revocation_csv, name="certificates_revocation_export_csv"),
    path("certificates_revocation/export/json/", views.export_certificates_revocation_json, name="certificates_revocation_export_json"),
]
