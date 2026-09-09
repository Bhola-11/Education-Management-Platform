"""
URL Routes for Enrollment: Prerequisite Enforcement
"""

from django.urls import path
from enrollment import views_enrollment_prereq_check as views

app_name = "enrollment"

urlpatterns = [
    path("enrollment_prereq_check/", views.EnrollmentPrereqCheckListView.as_view(), name="enrollment_prereq_check_list"),
    path("enrollment_prereq_check/<int:pk>/", views.EnrollmentPrereqCheckDetailView.as_view(), name="enrollment_prereq_check_detail"),
    path("enrollment_prereq_check/create/", views.EnrollmentPrereqCheckCreateView.as_view(), name="enrollment_prereq_check_create"),
    path("enrollment_prereq_check/<int:pk>/edit/", views.EnrollmentPrereqCheckUpdateView.as_view(), name="enrollment_prereq_check_update"),
    path("enrollment_prereq_check/<int:pk>/delete/", views.EnrollmentPrereqCheckDeleteView.as_view(), name="enrollment_prereq_check_delete"),
    path("enrollment_prereq_check/<int:pk>/print/", views.EnrollmentPrereqCheckPrintView.as_view(), name="enrollment_prereq_check_print"),
    path("enrollment_prereq_check/analytics/", views.EnrollmentPrereqCheckAnalyticsView.as_view(), name="enrollment_prereq_check_analytics"),
    path("enrollment_prereq_check/export/csv/", views.export_enrollment_prereq_check_csv, name="enrollment_prereq_check_export_csv"),
    path("enrollment_prereq_check/export/json/", views.export_enrollment_prereq_check_json, name="enrollment_prereq_check_export_json"),
]
