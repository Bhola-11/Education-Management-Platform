"""
URL Routes for Grading: GPA/CGPA Calculation
"""

from django.urls import path
from grading import views_grading_gpa_engine as views

app_name = "grading"

urlpatterns = [
    path("grading_gpa_engine/", views.GradingGpaEngineListView.as_view(), name="grading_gpa_engine_list"),
    path("grading_gpa_engine/<int:pk>/", views.GradingGpaEngineDetailView.as_view(), name="grading_gpa_engine_detail"),
    path("grading_gpa_engine/create/", views.GradingGpaEngineCreateView.as_view(), name="grading_gpa_engine_create"),
    path("grading_gpa_engine/<int:pk>/edit/", views.GradingGpaEngineUpdateView.as_view(), name="grading_gpa_engine_update"),
    path("grading_gpa_engine/<int:pk>/delete/", views.GradingGpaEngineDeleteView.as_view(), name="grading_gpa_engine_delete"),
    path("grading_gpa_engine/<int:pk>/print/", views.GradingGpaEnginePrintView.as_view(), name="grading_gpa_engine_print"),
    path("grading_gpa_engine/analytics/", views.GradingGpaEngineAnalyticsView.as_view(), name="grading_gpa_engine_analytics"),
    path("grading_gpa_engine/export/csv/", views.export_grading_gpa_engine_csv, name="grading_gpa_engine_export_csv"),
    path("grading_gpa_engine/export/json/", views.export_grading_gpa_engine_json, name="grading_gpa_engine_export_json"),
]
