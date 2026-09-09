"""
URL Routes for Core: Production Readiness
"""

from django.urls import path
from core import views_production_readiness as views

app_name = "core"

urlpatterns = [
    path("production_readiness/", views.ProductionReadinessListView.as_view(), name="production_readiness_list"),
    path("production_readiness/<int:pk>/", views.ProductionReadinessDetailView.as_view(), name="production_readiness_detail"),
    path("production_readiness/create/", views.ProductionReadinessCreateView.as_view(), name="production_readiness_create"),
    path("production_readiness/<int:pk>/edit/", views.ProductionReadinessUpdateView.as_view(), name="production_readiness_update"),
    path("production_readiness/<int:pk>/delete/", views.ProductionReadinessDeleteView.as_view(), name="production_readiness_delete"),
    path("production_readiness/<int:pk>/print/", views.ProductionReadinessPrintView.as_view(), name="production_readiness_print"),
    path("production_readiness/analytics/", views.ProductionReadinessAnalyticsView.as_view(), name="production_readiness_analytics"),
    path("production_readiness/export/csv/", views.export_production_readiness_csv, name="production_readiness_export_csv"),
    path("production_readiness/export/json/", views.export_production_readiness_json, name="production_readiness_export_json"),
]
