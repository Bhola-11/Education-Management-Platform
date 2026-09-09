"""
URL Routes for Enrollment: Admissions Pipeline
"""

from django.urls import path
from enrollment import views_enrollment_admissions as views

app_name = "enrollment"

urlpatterns = [
    path("enrollment_admissions/", views.EnrollmentAdmissionsListView.as_view(), name="enrollment_admissions_list"),
    path("enrollment_admissions/<int:pk>/", views.EnrollmentAdmissionsDetailView.as_view(), name="enrollment_admissions_detail"),
    path("enrollment_admissions/create/", views.EnrollmentAdmissionsCreateView.as_view(), name="enrollment_admissions_create"),
    path("enrollment_admissions/<int:pk>/edit/", views.EnrollmentAdmissionsUpdateView.as_view(), name="enrollment_admissions_update"),
    path("enrollment_admissions/<int:pk>/delete/", views.EnrollmentAdmissionsDeleteView.as_view(), name="enrollment_admissions_delete"),
    path("enrollment_admissions/<int:pk>/print/", views.EnrollmentAdmissionsPrintView.as_view(), name="enrollment_admissions_print"),
    path("enrollment_admissions/analytics/", views.EnrollmentAdmissionsAnalyticsView.as_view(), name="enrollment_admissions_analytics"),
    path("enrollment_admissions/export/csv/", views.export_enrollment_admissions_csv, name="enrollment_admissions_export_csv"),
    path("enrollment_admissions/export/json/", views.export_enrollment_admissions_json, name="enrollment_admissions_export_json"),
]
