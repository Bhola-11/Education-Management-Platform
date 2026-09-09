"""
URL Routes for Timetables: Time Slot Architecture
"""

from django.urls import path
from timetables import views_timetables_slots as views

app_name = "timetables"

urlpatterns = [
    path("timetables_slots/", views.TimetablesSlotsListView.as_view(), name="timetables_slots_list"),
    path("timetables_slots/<int:pk>/", views.TimetablesSlotsDetailView.as_view(), name="timetables_slots_detail"),
    path("timetables_slots/create/", views.TimetablesSlotsCreateView.as_view(), name="timetables_slots_create"),
    path("timetables_slots/<int:pk>/edit/", views.TimetablesSlotsUpdateView.as_view(), name="timetables_slots_update"),
    path("timetables_slots/<int:pk>/delete/", views.TimetablesSlotsDeleteView.as_view(), name="timetables_slots_delete"),
    path("timetables_slots/<int:pk>/print/", views.TimetablesSlotsPrintView.as_view(), name="timetables_slots_print"),
    path("timetables_slots/analytics/", views.TimetablesSlotsAnalyticsView.as_view(), name="timetables_slots_analytics"),
    path("timetables_slots/export/csv/", views.export_timetables_slots_csv, name="timetables_slots_export_csv"),
    path("timetables_slots/export/json/", views.export_timetables_slots_json, name="timetables_slots_export_json"),
]
