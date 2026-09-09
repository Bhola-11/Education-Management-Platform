"""
URL Routes for Academics: Subject Architecture
"""

from django.urls import path
from academics import views_academics_subjects as views

app_name = "academics"

urlpatterns = [
    path("academics_subjects/", views.AcademicsSubjectsListView.as_view(), name="academics_subjects_list"),
    path("academics_subjects/<int:pk>/", views.AcademicsSubjectsDetailView.as_view(), name="academics_subjects_detail"),
    path("academics_subjects/create/", views.AcademicsSubjectsCreateView.as_view(), name="academics_subjects_create"),
    path("academics_subjects/<int:pk>/edit/", views.AcademicsSubjectsUpdateView.as_view(), name="academics_subjects_update"),
    path("academics_subjects/<int:pk>/delete/", views.AcademicsSubjectsDeleteView.as_view(), name="academics_subjects_delete"),
    path("academics_subjects/<int:pk>/print/", views.AcademicsSubjectsPrintView.as_view(), name="academics_subjects_print"),
    path("academics_subjects/analytics/", views.AcademicsSubjectsAnalyticsView.as_view(), name="academics_subjects_analytics"),
    path("academics_subjects/export/csv/", views.export_academics_subjects_csv, name="academics_subjects_export_csv"),
    path("academics_subjects/export/json/", views.export_academics_subjects_json, name="academics_subjects_export_json"),
]
