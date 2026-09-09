"""
URL Routes for Core: Global Search Indexer
"""

from django.urls import path
from core import views_core_global_search as views

app_name = "core"

urlpatterns = [
    path("core_global_search/", views.CoreGlobalSearchListView.as_view(), name="core_global_search_list"),
    path("core_global_search/<int:pk>/", views.CoreGlobalSearchDetailView.as_view(), name="core_global_search_detail"),
    path("core_global_search/create/", views.CoreGlobalSearchCreateView.as_view(), name="core_global_search_create"),
    path("core_global_search/<int:pk>/edit/", views.CoreGlobalSearchUpdateView.as_view(), name="core_global_search_update"),
    path("core_global_search/<int:pk>/delete/", views.CoreGlobalSearchDeleteView.as_view(), name="core_global_search_delete"),
    path("core_global_search/<int:pk>/print/", views.CoreGlobalSearchPrintView.as_view(), name="core_global_search_print"),
    path("core_global_search/analytics/", views.CoreGlobalSearchAnalyticsView.as_view(), name="core_global_search_analytics"),
    path("core_global_search/export/csv/", views.export_core_global_search_csv, name="core_global_search_export_csv"),
    path("core_global_search/export/json/", views.export_core_global_search_json, name="core_global_search_export_json"),
]
