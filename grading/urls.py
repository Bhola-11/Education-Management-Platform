"""
URL Routes for Grading: Marks Evaluation Sheet
"""

from django.urls import path
from grading import views_grading_marks_entry as views

app_name = "grading"

urlpatterns = [
    path("grading_marks_entry/", views.GradingMarksEntryListView.as_view(), name="grading_marks_entry_list"),
    path("grading_marks_entry/<int:pk>/", views.GradingMarksEntryDetailView.as_view(), name="grading_marks_entry_detail"),
    path("grading_marks_entry/create/", views.GradingMarksEntryCreateView.as_view(), name="grading_marks_entry_create"),
    path("grading_marks_entry/<int:pk>/edit/", views.GradingMarksEntryUpdateView.as_view(), name="grading_marks_entry_update"),
    path("grading_marks_entry/<int:pk>/delete/", views.GradingMarksEntryDeleteView.as_view(), name="grading_marks_entry_delete"),
    path("grading_marks_entry/<int:pk>/print/", views.GradingMarksEntryPrintView.as_view(), name="grading_marks_entry_print"),
    path("grading_marks_entry/analytics/", views.GradingMarksEntryAnalyticsView.as_view(), name="grading_marks_entry_analytics"),
    path("grading_marks_entry/export/csv/", views.export_grading_marks_entry_csv, name="grading_marks_entry_export_csv"),
    path("grading_marks_entry/export/json/", views.export_grading_marks_entry_json, name="grading_marks_entry_export_json"),
]
