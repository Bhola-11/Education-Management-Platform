"""
URL Routes for Analytics: Institutional Financial Analytics
"""

from django.urls import path
from analytics import views_analytics_financial as views

app_name = "analytics"

urlpatterns = [
    path("analytics_financial/", views.AnalyticsFinancialListView.as_view(), name="analytics_financial_list"),
    path("analytics_financial/<int:pk>/", views.AnalyticsFinancialDetailView.as_view(), name="analytics_financial_detail"),
    path("analytics_financial/create/", views.AnalyticsFinancialCreateView.as_view(), name="analytics_financial_create"),
    path("analytics_financial/<int:pk>/edit/", views.AnalyticsFinancialUpdateView.as_view(), name="analytics_financial_update"),
    path("analytics_financial/<int:pk>/delete/", views.AnalyticsFinancialDeleteView.as_view(), name="analytics_financial_delete"),
    path("analytics_financial/<int:pk>/print/", views.AnalyticsFinancialPrintView.as_view(), name="analytics_financial_print"),
    path("analytics_financial/analytics/", views.AnalyticsFinancialAnalyticsView.as_view(), name="analytics_financial_analytics"),
    path("analytics_financial/export/csv/", views.export_analytics_financial_csv, name="analytics_financial_export_csv"),
    path("analytics_financial/export/json/", views.export_analytics_financial_json, name="analytics_financial_export_json"),
]
