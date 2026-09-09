"""
URL Routes for Library: Book Circulation Desk
"""

from django.urls import path
from library import views_library_circulation as views

app_name = "library"

urlpatterns = [
    path("library_circulation/", views.LibraryCirculationListView.as_view(), name="library_circulation_list"),
    path("library_circulation/<int:pk>/", views.LibraryCirculationDetailView.as_view(), name="library_circulation_detail"),
    path("library_circulation/create/", views.LibraryCirculationCreateView.as_view(), name="library_circulation_create"),
    path("library_circulation/<int:pk>/edit/", views.LibraryCirculationUpdateView.as_view(), name="library_circulation_update"),
    path("library_circulation/<int:pk>/delete/", views.LibraryCirculationDeleteView.as_view(), name="library_circulation_delete"),
    path("library_circulation/<int:pk>/print/", views.LibraryCirculationPrintView.as_view(), name="library_circulation_print"),
    path("library_circulation/analytics/", views.LibraryCirculationAnalyticsView.as_view(), name="library_circulation_analytics"),
    path("library_circulation/export/csv/", views.export_library_circulation_csv, name="library_circulation_export_csv"),
    path("library_circulation/export/json/", views.export_library_circulation_json, name="library_circulation_export_json"),
]
