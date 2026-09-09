"""
URL Routes for Certificates: Certificate Template Designer
"""

from django.urls import path
from certificates import views_certificates_templates as views

app_name = "certificates"

urlpatterns = [
    path("certificates_templates/", views.CertificatesTemplatesListView.as_view(), name="certificates_templates_list"),
    path("certificates_templates/<int:pk>/", views.CertificatesTemplatesDetailView.as_view(), name="certificates_templates_detail"),
    path("certificates_templates/create/", views.CertificatesTemplatesCreateView.as_view(), name="certificates_templates_create"),
    path("certificates_templates/<int:pk>/edit/", views.CertificatesTemplatesUpdateView.as_view(), name="certificates_templates_update"),
    path("certificates_templates/<int:pk>/delete/", views.CertificatesTemplatesDeleteView.as_view(), name="certificates_templates_delete"),
    path("certificates_templates/<int:pk>/print/", views.CertificatesTemplatesPrintView.as_view(), name="certificates_templates_print"),
    path("certificates_templates/analytics/", views.CertificatesTemplatesAnalyticsView.as_view(), name="certificates_templates_analytics"),
    path("certificates_templates/export/csv/", views.export_certificates_templates_csv, name="certificates_templates_export_csv"),
    path("certificates_templates/export/json/", views.export_certificates_templates_json, name="certificates_templates_export_json"),
]
