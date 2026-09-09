"""
URL Routes for Students: Students & Enrollment Tests
"""

from django.urls import path
from students import views_students_and_enrollment_suite as views

app_name = "students"

urlpatterns = [
    path("students_and_enrollment_suite/", views.StudentsAndEnrollmentSuiteListView.as_view(), name="students_and_enrollment_suite_list"),
    path("students_and_enrollment_suite/<int:pk>/", views.StudentsAndEnrollmentSuiteDetailView.as_view(), name="students_and_enrollment_suite_detail"),
    path("students_and_enrollment_suite/create/", views.StudentsAndEnrollmentSuiteCreateView.as_view(), name="students_and_enrollment_suite_create"),
    path("students_and_enrollment_suite/<int:pk>/edit/", views.StudentsAndEnrollmentSuiteUpdateView.as_view(), name="students_and_enrollment_suite_update"),
    path("students_and_enrollment_suite/<int:pk>/delete/", views.StudentsAndEnrollmentSuiteDeleteView.as_view(), name="students_and_enrollment_suite_delete"),
    path("students_and_enrollment_suite/<int:pk>/print/", views.StudentsAndEnrollmentSuitePrintView.as_view(), name="students_and_enrollment_suite_print"),
    path("students_and_enrollment_suite/analytics/", views.StudentsAndEnrollmentSuiteAnalyticsView.as_view(), name="students_and_enrollment_suite_analytics"),
    path("students_and_enrollment_suite/export/csv/", views.export_students_and_enrollment_suite_csv, name="students_and_enrollment_suite_export_csv"),
    path("students_and_enrollment_suite/export/json/", views.export_students_and_enrollment_suite_json, name="students_and_enrollment_suite_export_json"),
]
