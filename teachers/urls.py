"""
URL Routes for Teachers: Faculty Credentials
"""

from django.urls import path
from teachers import views_teachers_credentials as views

app_name = "teachers"

urlpatterns = [
    path("teachers_credentials/", views.TeachersCredentialsListView.as_view(), name="teachers_credentials_list"),
    path("teachers_credentials/<int:pk>/", views.TeachersCredentialsDetailView.as_view(), name="teachers_credentials_detail"),
    path("teachers_credentials/create/", views.TeachersCredentialsCreateView.as_view(), name="teachers_credentials_create"),
    path("teachers_credentials/<int:pk>/edit/", views.TeachersCredentialsUpdateView.as_view(), name="teachers_credentials_update"),
    path("teachers_credentials/<int:pk>/delete/", views.TeachersCredentialsDeleteView.as_view(), name="teachers_credentials_delete"),
    path("teachers_credentials/<int:pk>/print/", views.TeachersCredentialsPrintView.as_view(), name="teachers_credentials_print"),
    path("teachers_credentials/analytics/", views.TeachersCredentialsAnalyticsView.as_view(), name="teachers_credentials_analytics"),
    path("teachers_credentials/export/csv/", views.export_teachers_credentials_csv, name="teachers_credentials_export_csv"),
    path("teachers_credentials/export/json/", views.export_teachers_credentials_json, name="teachers_credentials_export_json"),
]
