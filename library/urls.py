"""
URL Routes for Library: Reservations & Holds
"""

from django.urls import path
from library import views_library_reservations as views

app_name = "library"

urlpatterns = [
    path("library_reservations/", views.LibraryReservationsListView.as_view(), name="library_reservations_list"),
    path("library_reservations/<int:pk>/", views.LibraryReservationsDetailView.as_view(), name="library_reservations_detail"),
    path("library_reservations/create/", views.LibraryReservationsCreateView.as_view(), name="library_reservations_create"),
    path("library_reservations/<int:pk>/edit/", views.LibraryReservationsUpdateView.as_view(), name="library_reservations_update"),
    path("library_reservations/<int:pk>/delete/", views.LibraryReservationsDeleteView.as_view(), name="library_reservations_delete"),
    path("library_reservations/<int:pk>/print/", views.LibraryReservationsPrintView.as_view(), name="library_reservations_print"),
    path("library_reservations/analytics/", views.LibraryReservationsAnalyticsView.as_view(), name="library_reservations_analytics"),
    path("library_reservations/export/csv/", views.export_library_reservations_csv, name="library_reservations_export_csv"),
    path("library_reservations/export/json/", views.export_library_reservations_json, name="library_reservations_export_json"),
]
