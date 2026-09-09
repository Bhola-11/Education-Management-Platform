"""
URL Routes for Attendance: Attendance Threshold Alerts
"""

from django.urls import path
from attendance import views_attendance_alerts as views

app_name = "attendance"

urlpatterns = [
    path("attendance_alerts/", views.AttendanceAlertsListView.as_view(), name="attendance_alerts_list"),
    path("attendance_alerts/<int:pk>/", views.AttendanceAlertsDetailView.as_view(), name="attendance_alerts_detail"),
    path("attendance_alerts/create/", views.AttendanceAlertsCreateView.as_view(), name="attendance_alerts_create"),
    path("attendance_alerts/<int:pk>/edit/", views.AttendanceAlertsUpdateView.as_view(), name="attendance_alerts_update"),
    path("attendance_alerts/<int:pk>/delete/", views.AttendanceAlertsDeleteView.as_view(), name="attendance_alerts_delete"),
    path("attendance_alerts/<int:pk>/print/", views.AttendanceAlertsPrintView.as_view(), name="attendance_alerts_print"),
    path("attendance_alerts/analytics/", views.AttendanceAlertsAnalyticsView.as_view(), name="attendance_alerts_analytics"),
    path("attendance_alerts/export/csv/", views.export_attendance_alerts_csv, name="attendance_alerts_export_csv"),
    path("attendance_alerts/export/json/", views.export_attendance_alerts_json, name="attendance_alerts_export_json"),
]
