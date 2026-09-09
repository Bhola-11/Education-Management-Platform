"""
URL Routes for Dashboards: Executive Dashboard
"""

from django.urls import path
from dashboards import views_dashboards_admin as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_admin/", views.DashboardsAdminListView.as_view(), name="dashboards_admin_list"),
    path("dashboards_admin/<int:pk>/", views.DashboardsAdminDetailView.as_view(), name="dashboards_admin_detail"),
    path("dashboards_admin/create/", views.DashboardsAdminCreateView.as_view(), name="dashboards_admin_create"),
    path("dashboards_admin/<int:pk>/edit/", views.DashboardsAdminUpdateView.as_view(), name="dashboards_admin_update"),
    path("dashboards_admin/<int:pk>/delete/", views.DashboardsAdminDeleteView.as_view(), name="dashboards_admin_delete"),
    path("dashboards_admin/<int:pk>/print/", views.DashboardsAdminPrintView.as_view(), name="dashboards_admin_print"),
    path("dashboards_admin/analytics/", views.DashboardsAdminAnalyticsView.as_view(), name="dashboards_admin_analytics"),
    path("dashboards_admin/export/csv/", views.export_dashboards_admin_csv, name="dashboards_admin_export_csv"),
    path("dashboards_admin/export/json/", views.export_dashboards_admin_json, name="dashboards_admin_export_json"),
]
