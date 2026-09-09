"""
URL Routes for Attendance: Daily Student Attendance
"""

from django.urls import path
from attendance import views_attendance_daily_student as views

app_name = "attendance"

urlpatterns = [
    path("attendance_daily_student/", views.AttendanceDailyStudentListView.as_view(), name="attendance_daily_student_list"),
    path("attendance_daily_student/<int:pk>/", views.AttendanceDailyStudentDetailView.as_view(), name="attendance_daily_student_detail"),
    path("attendance_daily_student/create/", views.AttendanceDailyStudentCreateView.as_view(), name="attendance_daily_student_create"),
    path("attendance_daily_student/<int:pk>/edit/", views.AttendanceDailyStudentUpdateView.as_view(), name="attendance_daily_student_update"),
    path("attendance_daily_student/<int:pk>/delete/", views.AttendanceDailyStudentDeleteView.as_view(), name="attendance_daily_student_delete"),
    path("attendance_daily_student/<int:pk>/print/", views.AttendanceDailyStudentPrintView.as_view(), name="attendance_daily_student_print"),
    path("attendance_daily_student/analytics/", views.AttendanceDailyStudentAnalyticsView.as_view(), name="attendance_daily_student_analytics"),
    path("attendance_daily_student/export/csv/", views.export_attendance_daily_student_csv, name="attendance_daily_student_export_csv"),
    path("attendance_daily_student/export/json/", views.export_attendance_daily_student_json, name="attendance_daily_student_export_json"),
]
