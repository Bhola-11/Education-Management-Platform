"""
URL Routes for Dashboards: Bursar Financial Hub
"""

from django.urls import path
from dashboards import views_dashboards_finance as views

app_name = "dashboards"

urlpatterns = [
    path("dashboards_finance/", views.DashboardsFinanceListView.as_view(), name="dashboards_finance_list"),
    path("dashboards_finance/<int:pk>/", views.DashboardsFinanceDetailView.as_view(), name="dashboards_finance_detail"),
    path("dashboards_finance/create/", views.DashboardsFinanceCreateView.as_view(), name="dashboards_finance_create"),
    path("dashboards_finance/<int:pk>/edit/", views.DashboardsFinanceUpdateView.as_view(), name="dashboards_finance_update"),
    path("dashboards_finance/<int:pk>/delete/", views.DashboardsFinanceDeleteView.as_view(), name="dashboards_finance_delete"),
    path("dashboards_finance/<int:pk>/print/", views.DashboardsFinancePrintView.as_view(), name="dashboards_finance_print"),
    path("dashboards_finance/analytics/", views.DashboardsFinanceAnalyticsView.as_view(), name="dashboards_finance_analytics"),
    path("dashboards_finance/export/csv/", views.export_dashboards_finance_csv, name="dashboards_finance_export_csv"),
    path("dashboards_finance/export/json/", views.export_dashboards_finance_json, name="dashboards_finance_export_json"),
]
