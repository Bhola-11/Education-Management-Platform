"""
URL Routes for Timetables: Schedule Conflict Solver
"""

from django.urls import path
from timetables import views_timetables_conflict_detector as views

app_name = "timetables"

urlpatterns = [
    path("timetables_conflict_detector/", views.TimetablesConflictDetectorListView.as_view(), name="timetables_conflict_detector_list"),
    path("timetables_conflict_detector/<int:pk>/", views.TimetablesConflictDetectorDetailView.as_view(), name="timetables_conflict_detector_detail"),
    path("timetables_conflict_detector/create/", views.TimetablesConflictDetectorCreateView.as_view(), name="timetables_conflict_detector_create"),
    path("timetables_conflict_detector/<int:pk>/edit/", views.TimetablesConflictDetectorUpdateView.as_view(), name="timetables_conflict_detector_update"),
    path("timetables_conflict_detector/<int:pk>/delete/", views.TimetablesConflictDetectorDeleteView.as_view(), name="timetables_conflict_detector_delete"),
    path("timetables_conflict_detector/<int:pk>/print/", views.TimetablesConflictDetectorPrintView.as_view(), name="timetables_conflict_detector_print"),
    path("timetables_conflict_detector/analytics/", views.TimetablesConflictDetectorAnalyticsView.as_view(), name="timetables_conflict_detector_analytics"),
    path("timetables_conflict_detector/export/csv/", views.export_timetables_conflict_detector_csv, name="timetables_conflict_detector_export_csv"),
    path("timetables_conflict_detector/export/json/", views.export_timetables_conflict_detector_json, name="timetables_conflict_detector_export_json"),
]
