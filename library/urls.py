"""
URL Routes for Library: Library Cataloging
"""

from django.urls import path
from library import views_library_catalog as views

app_name = "library"

urlpatterns = [
    path("library_catalog/", views.LibraryCatalogListView.as_view(), name="library_catalog_list"),
    path("library_catalog/<int:pk>/", views.LibraryCatalogDetailView.as_view(), name="library_catalog_detail"),
    path("library_catalog/create/", views.LibraryCatalogCreateView.as_view(), name="library_catalog_create"),
    path("library_catalog/<int:pk>/edit/", views.LibraryCatalogUpdateView.as_view(), name="library_catalog_update"),
    path("library_catalog/<int:pk>/delete/", views.LibraryCatalogDeleteView.as_view(), name="library_catalog_delete"),
    path("library_catalog/<int:pk>/print/", views.LibraryCatalogPrintView.as_view(), name="library_catalog_print"),
    path("library_catalog/analytics/", views.LibraryCatalogAnalyticsView.as_view(), name="library_catalog_analytics"),
    path("library_catalog/export/csv/", views.export_library_catalog_csv, name="library_catalog_export_csv"),
    path("library_catalog/export/json/", views.export_library_catalog_json, name="library_catalog_export_json"),
]
