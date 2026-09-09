"""
URL Routes for Grading: Official Academic Transcripts
"""

from django.urls import path
from grading import views_grading_transcripts as views

app_name = "grading"

urlpatterns = [
    path("grading_transcripts/", views.GradingTranscriptsListView.as_view(), name="grading_transcripts_list"),
    path("grading_transcripts/<int:pk>/", views.GradingTranscriptsDetailView.as_view(), name="grading_transcripts_detail"),
    path("grading_transcripts/create/", views.GradingTranscriptsCreateView.as_view(), name="grading_transcripts_create"),
    path("grading_transcripts/<int:pk>/edit/", views.GradingTranscriptsUpdateView.as_view(), name="grading_transcripts_update"),
    path("grading_transcripts/<int:pk>/delete/", views.GradingTranscriptsDeleteView.as_view(), name="grading_transcripts_delete"),
    path("grading_transcripts/<int:pk>/print/", views.GradingTranscriptsPrintView.as_view(), name="grading_transcripts_print"),
    path("grading_transcripts/analytics/", views.GradingTranscriptsAnalyticsView.as_view(), name="grading_transcripts_analytics"),
    path("grading_transcripts/export/csv/", views.export_grading_transcripts_csv, name="grading_transcripts_export_csv"),
    path("grading_transcripts/export/json/", views.export_grading_transcripts_json, name="grading_transcripts_export_json"),
]
