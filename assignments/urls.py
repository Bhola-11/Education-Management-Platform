"""
URL Routes for Assignments: Evaluation Rubrics
"""

from django.urls import path
from assignments import views_assignments_rubrics as views

app_name = "assignments"

urlpatterns = [
    path("assignments_rubrics/", views.AssignmentsRubricsListView.as_view(), name="assignments_rubrics_list"),
    path("assignments_rubrics/<int:pk>/", views.AssignmentsRubricsDetailView.as_view(), name="assignments_rubrics_detail"),
    path("assignments_rubrics/create/", views.AssignmentsRubricsCreateView.as_view(), name="assignments_rubrics_create"),
    path("assignments_rubrics/<int:pk>/edit/", views.AssignmentsRubricsUpdateView.as_view(), name="assignments_rubrics_update"),
    path("assignments_rubrics/<int:pk>/delete/", views.AssignmentsRubricsDeleteView.as_view(), name="assignments_rubrics_delete"),
    path("assignments_rubrics/<int:pk>/print/", views.AssignmentsRubricsPrintView.as_view(), name="assignments_rubrics_print"),
    path("assignments_rubrics/analytics/", views.AssignmentsRubricsAnalyticsView.as_view(), name="assignments_rubrics_analytics"),
    path("assignments_rubrics/export/csv/", views.export_assignments_rubrics_csv, name="assignments_rubrics_export_csv"),
    path("assignments_rubrics/export/json/", views.export_assignments_rubrics_json, name="assignments_rubrics_export_json"),
]
