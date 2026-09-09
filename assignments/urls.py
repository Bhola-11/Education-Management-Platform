"""
URL Routes for Assignments: Assignment Specifications
"""

from django.urls import path
from assignments import views_assignments_core as views

app_name = "assignments"

urlpatterns = [
    path("assignments_core/", views.AssignmentsCoreListView.as_view(), name="assignments_core_list"),
    path("assignments_core/<int:pk>/", views.AssignmentsCoreDetailView.as_view(), name="assignments_core_detail"),
    path("assignments_core/create/", views.AssignmentsCoreCreateView.as_view(), name="assignments_core_create"),
    path("assignments_core/<int:pk>/edit/", views.AssignmentsCoreUpdateView.as_view(), name="assignments_core_update"),
    path("assignments_core/<int:pk>/delete/", views.AssignmentsCoreDeleteView.as_view(), name="assignments_core_delete"),
    path("assignments_core/<int:pk>/print/", views.AssignmentsCorePrintView.as_view(), name="assignments_core_print"),
    path("assignments_core/analytics/", views.AssignmentsCoreAnalyticsView.as_view(), name="assignments_core_analytics"),
    path("assignments_core/export/csv/", views.export_assignments_core_csv, name="assignments_core_export_csv"),
    path("assignments_core/export/json/", views.export_assignments_core_json, name="assignments_core_export_json"),
]
