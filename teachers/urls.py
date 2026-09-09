"""
URL Routes for Teachers: Faculty Workload
"""

from django.urls import path
from teachers import views_teachers_workload as views

app_name = "teachers"

urlpatterns = [
    path("teachers_workload/", views.TeachersWorkloadListView.as_view(), name="teachers_workload_list"),
    path("teachers_workload/<int:pk>/", views.TeachersWorkloadDetailView.as_view(), name="teachers_workload_detail"),
    path("teachers_workload/create/", views.TeachersWorkloadCreateView.as_view(), name="teachers_workload_create"),
    path("teachers_workload/<int:pk>/edit/", views.TeachersWorkloadUpdateView.as_view(), name="teachers_workload_update"),
    path("teachers_workload/<int:pk>/delete/", views.TeachersWorkloadDeleteView.as_view(), name="teachers_workload_delete"),
    path("teachers_workload/<int:pk>/print/", views.TeachersWorkloadPrintView.as_view(), name="teachers_workload_print"),
    path("teachers_workload/analytics/", views.TeachersWorkloadAnalyticsView.as_view(), name="teachers_workload_analytics"),
    path("teachers_workload/export/csv/", views.export_teachers_workload_csv, name="teachers_workload_export_csv"),
    path("teachers_workload/export/json/", views.export_teachers_workload_json, name="teachers_workload_export_json"),
]
