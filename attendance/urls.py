"""
URL Routes for Attendance: Leave Workflow
"""

from django.urls import path
from attendance import views_attendance_leave_workflow as views

app_name = "attendance"

urlpatterns = [
    path("attendance_leave_workflow/", views.AttendanceLeaveWorkflowListView.as_view(), name="attendance_leave_workflow_list"),
    path("attendance_leave_workflow/<int:pk>/", views.AttendanceLeaveWorkflowDetailView.as_view(), name="attendance_leave_workflow_detail"),
    path("attendance_leave_workflow/create/", views.AttendanceLeaveWorkflowCreateView.as_view(), name="attendance_leave_workflow_create"),
    path("attendance_leave_workflow/<int:pk>/edit/", views.AttendanceLeaveWorkflowUpdateView.as_view(), name="attendance_leave_workflow_update"),
    path("attendance_leave_workflow/<int:pk>/delete/", views.AttendanceLeaveWorkflowDeleteView.as_view(), name="attendance_leave_workflow_delete"),
    path("attendance_leave_workflow/<int:pk>/print/", views.AttendanceLeaveWorkflowPrintView.as_view(), name="attendance_leave_workflow_print"),
    path("attendance_leave_workflow/analytics/", views.AttendanceLeaveWorkflowAnalyticsView.as_view(), name="attendance_leave_workflow_analytics"),
    path("attendance_leave_workflow/export/csv/", views.export_attendance_leave_workflow_csv, name="attendance_leave_workflow_export_csv"),
    path("attendance_leave_workflow/export/json/", views.export_attendance_leave_workflow_json, name="attendance_leave_workflow_export_json"),
]
