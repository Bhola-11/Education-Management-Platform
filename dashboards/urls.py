"""
URL Routes for Dashboards: Student Self-Service Hub
"""

from django.urls import path
from dashboards import views_dashboards_student as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_student/", views.DashboardsStudentListView.as_view(), name="dashboards_student_list"),
    path("dashboards_student/<int:pk>/", views.DashboardsStudentDetailView.as_view(), name="dashboards_student_detail"),
    path("dashboards_student/create/", views.DashboardsStudentCreateView.as_view(), name="dashboards_student_create"),
    path("dashboards_student/<int:pk>/edit/", views.DashboardsStudentUpdateView.as_view(), name="dashboards_student_update"),
    path("dashboards_student/<int:pk>/delete/", views.DashboardsStudentDeleteView.as_view(), name="dashboards_student_delete"),
    path("dashboards_student/<int:pk>/print/", views.DashboardsStudentPrintView.as_view(), name="dashboards_student_print"),
    path("dashboards_student/analytics/", views.DashboardsStudentAnalyticsView.as_view(), name="dashboards_student_analytics"),
    path("dashboards_student/export/csv/", views.export_dashboards_student_csv, name="dashboards_student_export_csv"),
    path("dashboards_student/export/json/", views.export_dashboards_student_json, name="dashboards_student_export_json"),
]
