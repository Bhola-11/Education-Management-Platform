"""
URL Routes for Assignments: Assignment Grading
"""

from django.urls import path
from assignments import views_assignments_grading as views

app_name = "assignments"

urlpatterns = [
    path("assignments_grading/", views.AssignmentsGradingListView.as_view(), name="assignments_grading_list"),
    path("assignments_grading/<int:pk>/", views.AssignmentsGradingDetailView.as_view(), name="assignments_grading_detail"),
    path("assignments_grading/create/", views.AssignmentsGradingCreateView.as_view(), name="assignments_grading_create"),
    path("assignments_grading/<int:pk>/edit/", views.AssignmentsGradingUpdateView.as_view(), name="assignments_grading_update"),
    path("assignments_grading/<int:pk>/delete/", views.AssignmentsGradingDeleteView.as_view(), name="assignments_grading_delete"),
    path("assignments_grading/<int:pk>/print/", views.AssignmentsGradingPrintView.as_view(), name="assignments_grading_print"),
    path("assignments_grading/analytics/", views.AssignmentsGradingAnalyticsView.as_view(), name="assignments_grading_analytics"),
    path("assignments_grading/export/csv/", views.export_assignments_grading_csv, name="assignments_grading_export_csv"),
    path("assignments_grading/export/json/", views.export_assignments_grading_json, name="assignments_grading_export_json"),
]
