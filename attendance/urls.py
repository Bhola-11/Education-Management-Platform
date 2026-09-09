"""
URL Routes for Attendance: Period Attendance
"""

from django.urls import path
from attendance import views_attendance_period_level as views

app_name = "attendance"

urlpatterns = [
    path("attendance_period_level/", views.AttendancePeriodLevelListView.as_view(), name="attendance_period_level_list"),
    path("attendance_period_level/<int:pk>/", views.AttendancePeriodLevelDetailView.as_view(), name="attendance_period_level_detail"),
    path("attendance_period_level/create/", views.AttendancePeriodLevelCreateView.as_view(), name="attendance_period_level_create"),
    path("attendance_period_level/<int:pk>/edit/", views.AttendancePeriodLevelUpdateView.as_view(), name="attendance_period_level_update"),
    path("attendance_period_level/<int:pk>/delete/", views.AttendancePeriodLevelDeleteView.as_view(), name="attendance_period_level_delete"),
    path("attendance_period_level/<int:pk>/print/", views.AttendancePeriodLevelPrintView.as_view(), name="attendance_period_level_print"),
    path("attendance_period_level/analytics/", views.AttendancePeriodLevelAnalyticsView.as_view(), name="attendance_period_level_analytics"),
    path("attendance_period_level/export/csv/", views.export_attendance_period_level_csv, name="attendance_period_level_export_csv"),
    path("attendance_period_level/export/json/", views.export_attendance_period_level_json, name="attendance_period_level_export_json"),
]
