"""
URL Routes for Dashboards: Dean Academic Dashboard
"""

from django.urls import path
from dashboards import views_dashboards_principal as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_principal/", views.DashboardsPrincipalListView.as_view(), name="dashboards_principal_list"),
    path("dashboards_principal/<int:pk>/", views.DashboardsPrincipalDetailView.as_view(), name="dashboards_principal_detail"),
    path("dashboards_principal/create/", views.DashboardsPrincipalCreateView.as_view(), name="dashboards_principal_create"),
    path("dashboards_principal/<int:pk>/edit/", views.DashboardsPrincipalUpdateView.as_view(), name="dashboards_principal_update"),
    path("dashboards_principal/<int:pk>/delete/", views.DashboardsPrincipalDeleteView.as_view(), name="dashboards_principal_delete"),
    path("dashboards_principal/<int:pk>/print/", views.DashboardsPrincipalPrintView.as_view(), name="dashboards_principal_print"),
    path("dashboards_principal/analytics/", views.DashboardsPrincipalAnalyticsView.as_view(), name="dashboards_principal_analytics"),
    path("dashboards_principal/export/csv/", views.export_dashboards_principal_csv, name="dashboards_principal_export_csv"),
    path("dashboards_principal/export/json/", views.export_dashboards_principal_json, name="dashboards_principal_export_json"),
]
