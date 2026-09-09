"""
URL Routes for Analytics: Enterprise Export Pipeline
"""

from django.urls import path
from analytics import views_analytics_export_pipeline as views

app_name = "analytics"

urlpatterns = [
    path("analytics_export_pipeline/", views.AnalyticsExportPipelineListView.as_view(), name="analytics_export_pipeline_list"),
    path("analytics_export_pipeline/<int:pk>/", views.AnalyticsExportPipelineDetailView.as_view(), name="analytics_export_pipeline_detail"),
    path("analytics_export_pipeline/create/", views.AnalyticsExportPipelineCreateView.as_view(), name="analytics_export_pipeline_create"),
    path("analytics_export_pipeline/<int:pk>/edit/", views.AnalyticsExportPipelineUpdateView.as_view(), name="analytics_export_pipeline_update"),
    path("analytics_export_pipeline/<int:pk>/delete/", views.AnalyticsExportPipelineDeleteView.as_view(), name="analytics_export_pipeline_delete"),
    path("analytics_export_pipeline/<int:pk>/print/", views.AnalyticsExportPipelinePrintView.as_view(), name="analytics_export_pipeline_print"),
    path("analytics_export_pipeline/analytics/", views.AnalyticsExportPipelineAnalyticsView.as_view(), name="analytics_export_pipeline_analytics"),
    path("analytics_export_pipeline/export/csv/", views.export_analytics_export_pipeline_csv, name="analytics_export_pipeline_export_csv"),
    path("analytics_export_pipeline/export/json/", views.export_analytics_export_pipeline_json, name="analytics_export_pipeline_export_json"),
]
