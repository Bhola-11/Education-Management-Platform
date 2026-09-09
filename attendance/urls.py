"""
URL Routes for Attendance: Staff Timekeeping
"""

from django.urls import path
from attendance import views_attendance_staff as views

app_name = "attendance"

urlpatterns = [
    path("attendance_staff/", views.AttendanceStaffListView.as_view(), name="attendance_staff_list"),
    path("attendance_staff/<int:pk>/", views.AttendanceStaffDetailView.as_view(), name="attendance_staff_detail"),
    path("attendance_staff/create/", views.AttendanceStaffCreateView.as_view(), name="attendance_staff_create"),
    path("attendance_staff/<int:pk>/edit/", views.AttendanceStaffUpdateView.as_view(), name="attendance_staff_update"),
    path("attendance_staff/<int:pk>/delete/", views.AttendanceStaffDeleteView.as_view(), name="attendance_staff_delete"),
    path("attendance_staff/<int:pk>/print/", views.AttendanceStaffPrintView.as_view(), name="attendance_staff_print"),
    path("attendance_staff/analytics/", views.AttendanceStaffAnalyticsView.as_view(), name="attendance_staff_analytics"),
    path("attendance_staff/export/csv/", views.export_attendance_staff_csv, name="attendance_staff_export_csv"),
    path("attendance_staff/export/json/", views.export_attendance_staff_json, name="attendance_staff_export_json"),
]
