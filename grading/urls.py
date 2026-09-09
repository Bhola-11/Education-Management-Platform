"""
URL Routes for Grading: Rank Lists & Distinctions
"""

from django.urls import path
from grading import views_grading_rank_lists as views

app_name = "grading"

urlpatterns = [
    path("grading_rank_lists/", views.GradingRankListsListView.as_view(), name="grading_rank_lists_list"),
    path("grading_rank_lists/<int:pk>/", views.GradingRankListsDetailView.as_view(), name="grading_rank_lists_detail"),
    path("grading_rank_lists/create/", views.GradingRankListsCreateView.as_view(), name="grading_rank_lists_create"),
    path("grading_rank_lists/<int:pk>/edit/", views.GradingRankListsUpdateView.as_view(), name="grading_rank_lists_update"),
    path("grading_rank_lists/<int:pk>/delete/", views.GradingRankListsDeleteView.as_view(), name="grading_rank_lists_delete"),
    path("grading_rank_lists/<int:pk>/print/", views.GradingRankListsPrintView.as_view(), name="grading_rank_lists_print"),
    path("grading_rank_lists/analytics/", views.GradingRankListsAnalyticsView.as_view(), name="grading_rank_lists_analytics"),
    path("grading_rank_lists/export/csv/", views.export_grading_rank_lists_csv, name="grading_rank_lists_export_csv"),
    path("grading_rank_lists/export/json/", views.export_grading_rank_lists_json, name="grading_rank_lists_export_json"),
]
