"""
URL Routes for Academics: Programs & Degrees
"""

from django.urls import path
from academics import views_academics_programs as views

app_name = "academics"

urlpatterns = [
    path("academics_programs/", views.AcademicsProgramsListView.as_view(), name="academics_programs_list"),
    path("academics_programs/<int:pk>/", views.AcademicsProgramsDetailView.as_view(), name="academics_programs_detail"),
    path("academics_programs/create/", views.AcademicsProgramsCreateView.as_view(), name="academics_programs_create"),
    path("academics_programs/<int:pk>/edit/", views.AcademicsProgramsUpdateView.as_view(), name="academics_programs_update"),
    path("academics_programs/<int:pk>/delete/", views.AcademicsProgramsDeleteView.as_view(), name="academics_programs_delete"),
    path("academics_programs/<int:pk>/print/", views.AcademicsProgramsPrintView.as_view(), name="academics_programs_print"),
    path("academics_programs/analytics/", views.AcademicsProgramsAnalyticsView.as_view(), name="academics_programs_analytics"),
    path("academics_programs/export/csv/", views.export_academics_programs_csv, name="academics_programs_export_csv"),
    path("academics_programs/export/json/", views.export_academics_programs_json, name="academics_programs_export_json"),
]
