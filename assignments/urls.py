"""
URL Routes for Assignments: Academic Integrity
"""

from django.urls import path
from assignments import views_assignments_plagiarism as views

app_name = "assignments"

urlpatterns = [
    path("assignments_plagiarism/", views.AssignmentsPlagiarismListView.as_view(), name="assignments_plagiarism_list"),
    path("assignments_plagiarism/<int:pk>/", views.AssignmentsPlagiarismDetailView.as_view(), name="assignments_plagiarism_detail"),
    path("assignments_plagiarism/create/", views.AssignmentsPlagiarismCreateView.as_view(), name="assignments_plagiarism_create"),
    path("assignments_plagiarism/<int:pk>/edit/", views.AssignmentsPlagiarismUpdateView.as_view(), name="assignments_plagiarism_update"),
    path("assignments_plagiarism/<int:pk>/delete/", views.AssignmentsPlagiarismDeleteView.as_view(), name="assignments_plagiarism_delete"),
    path("assignments_plagiarism/<int:pk>/print/", views.AssignmentsPlagiarismPrintView.as_view(), name="assignments_plagiarism_print"),
    path("assignments_plagiarism/analytics/", views.AssignmentsPlagiarismAnalyticsView.as_view(), name="assignments_plagiarism_analytics"),
    path("assignments_plagiarism/export/csv/", views.export_assignments_plagiarism_csv, name="assignments_plagiarism_export_csv"),
    path("assignments_plagiarism/export/json/", views.export_assignments_plagiarism_json, name="assignments_plagiarism_export_json"),
]
