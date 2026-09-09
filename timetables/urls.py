"""
URL Routes for Timetables: Timetable Matrix
"""

from django.urls import path
from timetables import views_timetables_entry as views

app_name = "timetables"

urlpatterns = [
    path("timetables_entry/", views.TimetablesEntryListView.as_view(), name="timetables_entry_list"),
    path("timetables_entry/<int:pk>/", views.TimetablesEntryDetailView.as_view(), name="timetables_entry_detail"),
    path("timetables_entry/create/", views.TimetablesEntryCreateView.as_view(), name="timetables_entry_create"),
    path("timetables_entry/<int:pk>/edit/", views.TimetablesEntryUpdateView.as_view(), name="timetables_entry_update"),
    path("timetables_entry/<int:pk>/delete/", views.TimetablesEntryDeleteView.as_view(), name="timetables_entry_delete"),
    path("timetables_entry/<int:pk>/print/", views.TimetablesEntryPrintView.as_view(), name="timetables_entry_print"),
    path("timetables_entry/analytics/", views.TimetablesEntryAnalyticsView.as_view(), name="timetables_entry_analytics"),
    path("timetables_entry/export/csv/", views.export_timetables_entry_csv, name="timetables_entry_export_csv"),
    path("timetables_entry/export/json/", views.export_timetables_entry_json, name="timetables_entry_export_json"),
]
