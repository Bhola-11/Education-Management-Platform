"""
URL Routes for Grading: Marks Moderation Workflow
"""

from django.urls import path
from grading import views_grading_moderation as views

app_name = "grading"

urlpatterns = [
    path("grading_moderation/", views.GradingModerationListView.as_view(), name="grading_moderation_list"),
    path("grading_moderation/<int:pk>/", views.GradingModerationDetailView.as_view(), name="grading_moderation_detail"),
    path("grading_moderation/create/", views.GradingModerationCreateView.as_view(), name="grading_moderation_create"),
    path("grading_moderation/<int:pk>/edit/", views.GradingModerationUpdateView.as_view(), name="grading_moderation_update"),
    path("grading_moderation/<int:pk>/delete/", views.GradingModerationDeleteView.as_view(), name="grading_moderation_delete"),
    path("grading_moderation/<int:pk>/print/", views.GradingModerationPrintView.as_view(), name="grading_moderation_print"),
    path("grading_moderation/analytics/", views.GradingModerationAnalyticsView.as_view(), name="grading_moderation_analytics"),
    path("grading_moderation/export/csv/", views.export_grading_moderation_csv, name="grading_moderation_export_csv"),
    path("grading_moderation/export/json/", views.export_grading_moderation_json, name="grading_moderation_export_json"),
]
