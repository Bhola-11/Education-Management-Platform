"""
URL Routes for Library: Library Overdue Fines
"""

from django.urls import path
from library import views_library_fines as views

app_name = "library"

urlpatterns = [
    path("library_fines/", views.LibraryFinesListView.as_view(), name="library_fines_list"),
    path("library_fines/<int:pk>/", views.LibraryFinesDetailView.as_view(), name="library_fines_detail"),
    path("library_fines/create/", views.LibraryFinesCreateView.as_view(), name="library_fines_create"),
    path("library_fines/<int:pk>/edit/", views.LibraryFinesUpdateView.as_view(), name="library_fines_update"),
    path("library_fines/<int:pk>/delete/", views.LibraryFinesDeleteView.as_view(), name="library_fines_delete"),
    path("library_fines/<int:pk>/print/", views.LibraryFinesPrintView.as_view(), name="library_fines_print"),
    path("library_fines/analytics/", views.LibraryFinesAnalyticsView.as_view(), name="library_fines_analytics"),
    path("library_fines/export/csv/", views.export_library_fines_csv, name="library_fines_export_csv"),
    path("library_fines/export/json/", views.export_library_fines_json, name="library_fines_export_json"),
]
