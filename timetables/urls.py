"""
URL Routes for Timetables: Timetable Visualizer
"""

from django.urls import path
from timetables import views_timetables_views_grid as views

app_name = "timetables"

urlpatterns = [
    path("timetables_views_grid/", views.TimetablesViewsGridListView.as_view(), name="timetables_views_grid_list"),
    path("timetables_views_grid/<int:pk>/", views.TimetablesViewsGridDetailView.as_view(), name="timetables_views_grid_detail"),
    path("timetables_views_grid/create/", views.TimetablesViewsGridCreateView.as_view(), name="timetables_views_grid_create"),
    path("timetables_views_grid/<int:pk>/edit/", views.TimetablesViewsGridUpdateView.as_view(), name="timetables_views_grid_update"),
    path("timetables_views_grid/<int:pk>/delete/", views.TimetablesViewsGridDeleteView.as_view(), name="timetables_views_grid_delete"),
    path("timetables_views_grid/<int:pk>/print/", views.TimetablesViewsGridPrintView.as_view(), name="timetables_views_grid_print"),
    path("timetables_views_grid/analytics/", views.TimetablesViewsGridAnalyticsView.as_view(), name="timetables_views_grid_analytics"),
    path("timetables_views_grid/export/csv/", views.export_timetables_views_grid_csv, name="timetables_views_grid_export_csv"),
    path("timetables_views_grid/export/json/", views.export_timetables_views_grid_json, name="timetables_views_grid_export_json"),
]
