"""
URL Routes for Attendance: Attendance Reporting
"""

from django.urls import path
from attendance import views_attendance_reports as views

app_name = "attendance"

urlpatterns = [
    path("attendance_reports/", views.AttendanceReportsListView.as_view(), name="attendance_reports_list"),
    path("attendance_reports/<int:pk>/", views.AttendanceReportsDetailView.as_view(), name="attendance_reports_detail"),
    path("attendance_reports/create/", views.AttendanceReportsCreateView.as_view(), name="attendance_reports_create"),
    path("attendance_reports/<int:pk>/edit/", views.AttendanceReportsUpdateView.as_view(), name="attendance_reports_update"),
    path("attendance_reports/<int:pk>/delete/", views.AttendanceReportsDeleteView.as_view(), name="attendance_reports_delete"),
    path("attendance_reports/<int:pk>/print/", views.AttendanceReportsPrintView.as_view(), name="attendance_reports_print"),
    path("attendance_reports/analytics/", views.AttendanceReportsAnalyticsView.as_view(), name="attendance_reports_analytics"),
    path("attendance_reports/export/csv/", views.export_attendance_reports_csv, name="attendance_reports_export_csv"),
    path("attendance_reports/export/json/", views.export_attendance_reports_json, name="attendance_reports_export_json"),
]
