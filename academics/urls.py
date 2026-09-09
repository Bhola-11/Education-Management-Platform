"""
URL Routes for Academics: Prerequisites & Rules
"""

from django.urls import path
from academics import views_academics_prerequisites as views

app_name = "academics"

urlpatterns = [
    path("academics_prerequisites/", views.AcademicsPrerequisitesListView.as_view(), name="academics_prerequisites_list"),
    path("academics_prerequisites/<int:pk>/", views.AcademicsPrerequisitesDetailView.as_view(), name="academics_prerequisites_detail"),
    path("academics_prerequisites/create/", views.AcademicsPrerequisitesCreateView.as_view(), name="academics_prerequisites_create"),
    path("academics_prerequisites/<int:pk>/edit/", views.AcademicsPrerequisitesUpdateView.as_view(), name="academics_prerequisites_update"),
    path("academics_prerequisites/<int:pk>/delete/", views.AcademicsPrerequisitesDeleteView.as_view(), name="academics_prerequisites_delete"),
    path("academics_prerequisites/<int:pk>/print/", views.AcademicsPrerequisitesPrintView.as_view(), name="academics_prerequisites_print"),
    path("academics_prerequisites/analytics/", views.AcademicsPrerequisitesAnalyticsView.as_view(), name="academics_prerequisites_analytics"),
    path("academics_prerequisites/export/csv/", views.export_academics_prerequisites_csv, name="academics_prerequisites_export_csv"),
    path("academics_prerequisites/export/json/", views.export_academics_prerequisites_json, name="academics_prerequisites_export_json"),
]
