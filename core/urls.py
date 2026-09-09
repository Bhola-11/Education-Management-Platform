"""
URL Routes for Core: Core Architecture
"""

from django.urls import path
from core import views_core_base_models as views

app_name = "core"

urlpatterns = [
    path("core_base_models/", views.CoreBaseModelsListView.as_view(), name="core_base_models_list"),
    path("core_base_models/<int:pk>/", views.CoreBaseModelsDetailView.as_view(), name="core_base_models_detail"),
    path("core_base_models/create/", views.CoreBaseModelsCreateView.as_view(), name="core_base_models_create"),
    path("core_base_models/<int:pk>/edit/", views.CoreBaseModelsUpdateView.as_view(), name="core_base_models_update"),
    path("core_base_models/<int:pk>/delete/", views.CoreBaseModelsDeleteView.as_view(), name="core_base_models_delete"),
    path("core_base_models/<int:pk>/print/", views.CoreBaseModelsPrintView.as_view(), name="core_base_models_print"),
    path("core_base_models/analytics/", views.CoreBaseModelsAnalyticsView.as_view(), name="core_base_models_analytics"),
    path("core_base_models/export/csv/", views.export_core_base_models_csv, name="core_base_models_export_csv"),
    path("core_base_models/export/json/", views.export_core_base_models_json, name="core_base_models_export_json"),
]
