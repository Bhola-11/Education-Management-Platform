"""
URL Routes for Grading: Grade Scales & Rules
"""

from django.urls import path
from grading import views_grading_scales as views

app_name = "grading"

urlpatterns = [
    path("grading_scales/", views.GradingScalesListView.as_view(), name="grading_scales_list"),
    path("grading_scales/<int:pk>/", views.GradingScalesDetailView.as_view(), name="grading_scales_detail"),
    path("grading_scales/create/", views.GradingScalesCreateView.as_view(), name="grading_scales_create"),
    path("grading_scales/<int:pk>/edit/", views.GradingScalesUpdateView.as_view(), name="grading_scales_update"),
    path("grading_scales/<int:pk>/delete/", views.GradingScalesDeleteView.as_view(), name="grading_scales_delete"),
    path("grading_scales/<int:pk>/print/", views.GradingScalesPrintView.as_view(), name="grading_scales_print"),
    path("grading_scales/analytics/", views.GradingScalesAnalyticsView.as_view(), name="grading_scales_analytics"),
    path("grading_scales/export/csv/", views.export_grading_scales_csv, name="grading_scales_export_csv"),
    path("grading_scales/export/json/", views.export_grading_scales_json, name="grading_scales_export_json"),
]
