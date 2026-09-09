"""
URL Routes for Dashboards: Faculty Workplace Hub
"""

from django.urls import path
from dashboards import views_dashboards_teacher as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_teacher/", views.DashboardsTeacherListView.as_view(), name="dashboards_teacher_list"),
    path("dashboards_teacher/<int:pk>/", views.DashboardsTeacherDetailView.as_view(), name="dashboards_teacher_detail"),
    path("dashboards_teacher/create/", views.DashboardsTeacherCreateView.as_view(), name="dashboards_teacher_create"),
    path("dashboards_teacher/<int:pk>/edit/", views.DashboardsTeacherUpdateView.as_view(), name="dashboards_teacher_update"),
    path("dashboards_teacher/<int:pk>/delete/", views.DashboardsTeacherDeleteView.as_view(), name="dashboards_teacher_delete"),
    path("dashboards_teacher/<int:pk>/print/", views.DashboardsTeacherPrintView.as_view(), name="dashboards_teacher_print"),
    path("dashboards_teacher/analytics/", views.DashboardsTeacherAnalyticsView.as_view(), name="dashboards_teacher_analytics"),
    path("dashboards_teacher/export/csv/", views.export_dashboards_teacher_csv, name="dashboards_teacher_export_csv"),
    path("dashboards_teacher/export/json/", views.export_dashboards_teacher_json, name="dashboards_teacher_export_json"),
]
