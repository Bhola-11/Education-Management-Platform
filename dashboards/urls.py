"""
URL Routes for Dashboards: Parent Family Portal
"""

from django.urls import path
from dashboards import views_dashboards_parent as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_parent/", views.DashboardsParentListView.as_view(), name="dashboards_parent_list"),
    path("dashboards_parent/<int:pk>/", views.DashboardsParentDetailView.as_view(), name="dashboards_parent_detail"),
    path("dashboards_parent/create/", views.DashboardsParentCreateView.as_view(), name="dashboards_parent_create"),
    path("dashboards_parent/<int:pk>/edit/", views.DashboardsParentUpdateView.as_view(), name="dashboards_parent_update"),
    path("dashboards_parent/<int:pk>/delete/", views.DashboardsParentDeleteView.as_view(), name="dashboards_parent_delete"),
    path("dashboards_parent/<int:pk>/print/", views.DashboardsParentPrintView.as_view(), name="dashboards_parent_print"),
    path("dashboards_parent/analytics/", views.DashboardsParentAnalyticsView.as_view(), name="dashboards_parent_analytics"),
    path("dashboards_parent/export/csv/", views.export_dashboards_parent_csv, name="dashboards_parent_export_csv"),
    path("dashboards_parent/export/json/", views.export_dashboards_parent_json, name="dashboards_parent_export_json"),
]
