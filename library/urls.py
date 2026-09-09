"""
URL Routes for Library: Physical Inventory
"""

from django.urls import path
from library import views_library_inventory as views

app_name = "library"

urlpatterns = [
    path("library_inventory/", views.LibraryInventoryListView.as_view(), name="library_inventory_list"),
    path("library_inventory/<int:pk>/", views.LibraryInventoryDetailView.as_view(), name="library_inventory_detail"),
    path("library_inventory/create/", views.LibraryInventoryCreateView.as_view(), name="library_inventory_create"),
    path("library_inventory/<int:pk>/edit/", views.LibraryInventoryUpdateView.as_view(), name="library_inventory_update"),
    path("library_inventory/<int:pk>/delete/", views.LibraryInventoryDeleteView.as_view(), name="library_inventory_delete"),
    path("library_inventory/<int:pk>/print/", views.LibraryInventoryPrintView.as_view(), name="library_inventory_print"),
    path("library_inventory/analytics/", views.LibraryInventoryAnalyticsView.as_view(), name="library_inventory_analytics"),
    path("library_inventory/export/csv/", views.export_library_inventory_csv, name="library_inventory_export_csv"),
    path("library_inventory/export/json/", views.export_library_inventory_json, name="library_inventory_export_json"),
]
