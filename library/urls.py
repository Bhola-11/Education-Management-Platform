"""
URL Routes for Library: OPAC Public Catalog
"""

from django.urls import path
from library import views_library_opac_views as views

app_name = "library"

urlpatterns = [
    path("library_opac_views/", views.LibraryOpacViewsListView.as_view(), name="library_opac_views_list"),
    path("library_opac_views/<int:pk>/", views.LibraryOpacViewsDetailView.as_view(), name="library_opac_views_detail"),
    path("library_opac_views/create/", views.LibraryOpacViewsCreateView.as_view(), name="library_opac_views_create"),
    path("library_opac_views/<int:pk>/edit/", views.LibraryOpacViewsUpdateView.as_view(), name="library_opac_views_update"),
    path("library_opac_views/<int:pk>/delete/", views.LibraryOpacViewsDeleteView.as_view(), name="library_opac_views_delete"),
    path("library_opac_views/<int:pk>/print/", views.LibraryOpacViewsPrintView.as_view(), name="library_opac_views_print"),
    path("library_opac_views/analytics/", views.LibraryOpacViewsAnalyticsView.as_view(), name="library_opac_views_analytics"),
    path("library_opac_views/export/csv/", views.export_library_opac_views_csv, name="library_opac_views_export_csv"),
    path("library_opac_views/export/json/", views.export_library_opac_views_json, name="library_opac_views_export_json"),
]
