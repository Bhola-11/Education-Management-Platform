"""
URL Routes for Certificates: Cryptographic Verification
"""

from django.urls import path
from certificates import views_certificates_verification as views

app_name = "certificates"

urlpatterns = [
    path("certificates_verification/", views.CertificatesVerificationListView.as_view(), name="certificates_verification_list"),
    path("certificates_verification/<int:pk>/", views.CertificatesVerificationDetailView.as_view(), name="certificates_verification_detail"),
    path("certificates_verification/create/", views.CertificatesVerificationCreateView.as_view(), name="certificates_verification_create"),
    path("certificates_verification/<int:pk>/edit/", views.CertificatesVerificationUpdateView.as_view(), name="certificates_verification_update"),
    path("certificates_verification/<int:pk>/delete/", views.CertificatesVerificationDeleteView.as_view(), name="certificates_verification_delete"),
    path("certificates_verification/<int:pk>/print/", views.CertificatesVerificationPrintView.as_view(), name="certificates_verification_print"),
    path("certificates_verification/analytics/", views.CertificatesVerificationAnalyticsView.as_view(), name="certificates_verification_analytics"),
    path("certificates_verification/export/csv/", views.export_certificates_verification_csv, name="certificates_verification_export_csv"),
    path("certificates_verification/export/json/", views.export_certificates_verification_json, name="certificates_verification_export_json"),
]
