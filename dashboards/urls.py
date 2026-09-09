"""
URL Routes for Dashboards: Librarian Ops Hub
"""

from django.urls import path
from dashboards import views_dashboards_librarian as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_librarian/", views.DashboardsLibrarianListView.as_view(), name="dashboards_librarian_list"),
    path("dashboards_librarian/<int:pk>/", views.DashboardsLibrarianDetailView.as_view(), name="dashboards_librarian_detail"),
    path("dashboards_librarian/create/", views.DashboardsLibrarianCreateView.as_view(), name="dashboards_librarian_create"),
    path("dashboards_librarian/<int:pk>/edit/", views.DashboardsLibrarianUpdateView.as_view(), name="dashboards_librarian_update"),
    path("dashboards_librarian/<int:pk>/delete/", views.DashboardsLibrarianDeleteView.as_view(), name="dashboards_librarian_delete"),
    path("dashboards_librarian/<int:pk>/print/", views.DashboardsLibrarianPrintView.as_view(), name="dashboards_librarian_print"),
    path("dashboards_librarian/analytics/", views.DashboardsLibrarianAnalyticsView.as_view(), name="dashboards_librarian_analytics"),
    path("dashboards_librarian/export/csv/", views.export_dashboards_librarian_csv, name="dashboards_librarian_export_csv"),
    path("dashboards_librarian/export/json/", views.export_dashboards_librarian_json, name="dashboards_librarian_export_json"),
]
