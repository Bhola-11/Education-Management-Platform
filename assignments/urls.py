"""
URL Routes for Assignments: Student Submissions
"""

from django.urls import path
from assignments import views_assignments_submissions as views

app_name = "assignments"

urlpatterns = [
    path("assignments_submissions/", views.AssignmentsSubmissionsListView.as_view(), name="assignments_submissions_list"),
    path("assignments_submissions/<int:pk>/", views.AssignmentsSubmissionsDetailView.as_view(), name="assignments_submissions_detail"),
    path("assignments_submissions/create/", views.AssignmentsSubmissionsCreateView.as_view(), name="assignments_submissions_create"),
    path("assignments_submissions/<int:pk>/edit/", views.AssignmentsSubmissionsUpdateView.as_view(), name="assignments_submissions_update"),
    path("assignments_submissions/<int:pk>/delete/", views.AssignmentsSubmissionsDeleteView.as_view(), name="assignments_submissions_delete"),
    path("assignments_submissions/<int:pk>/print/", views.AssignmentsSubmissionsPrintView.as_view(), name="assignments_submissions_print"),
    path("assignments_submissions/analytics/", views.AssignmentsSubmissionsAnalyticsView.as_view(), name="assignments_submissions_analytics"),
    path("assignments_submissions/export/csv/", views.export_assignments_submissions_csv, name="assignments_submissions_export_csv"),
    path("assignments_submissions/export/json/", views.export_assignments_submissions_json, name="assignments_submissions_export_json"),
]
