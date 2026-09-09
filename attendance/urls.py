"""
URL Routes for Attendance: Attendance & Exams Tests
"""

from django.urls import path
from attendance import views_attendance_and_exams_suite as views

app_name = "attendance"

urlpatterns = [
    path("attendance_and_exams_suite/", views.AttendanceAndExamsSuiteListView.as_view(), name="attendance_and_exams_suite_list"),
    path("attendance_and_exams_suite/<int:pk>/", views.AttendanceAndExamsSuiteDetailView.as_view(), name="attendance_and_exams_suite_detail"),
    path("attendance_and_exams_suite/create/", views.AttendanceAndExamsSuiteCreateView.as_view(), name="attendance_and_exams_suite_create"),
    path("attendance_and_exams_suite/<int:pk>/edit/", views.AttendanceAndExamsSuiteUpdateView.as_view(), name="attendance_and_exams_suite_update"),
    path("attendance_and_exams_suite/<int:pk>/delete/", views.AttendanceAndExamsSuiteDeleteView.as_view(), name="attendance_and_exams_suite_delete"),
    path("attendance_and_exams_suite/<int:pk>/print/", views.AttendanceAndExamsSuitePrintView.as_view(), name="attendance_and_exams_suite_print"),
    path("attendance_and_exams_suite/analytics/", views.AttendanceAndExamsSuiteAnalyticsView.as_view(), name="attendance_and_exams_suite_analytics"),
    path("attendance_and_exams_suite/export/csv/", views.export_attendance_and_exams_suite_csv, name="attendance_and_exams_suite_export_csv"),
    path("attendance_and_exams_suite/export/json/", views.export_attendance_and_exams_suite_json, name="attendance_and_exams_suite_export_json"),
]
