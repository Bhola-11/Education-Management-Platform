"""
URL Routes for Academics: Facilities & Classrooms
"""

from django.urls import path
from academics import views_academics_classrooms as views

app_name = "academics"

urlpatterns = [
    path("academics_classrooms/", views.AcademicsClassroomsListView.as_view(), name="academics_classrooms_list"),
    path("academics_classrooms/<int:pk>/", views.AcademicsClassroomsDetailView.as_view(), name="academics_classrooms_detail"),
    path("academics_classrooms/create/", views.AcademicsClassroomsCreateView.as_view(), name="academics_classrooms_create"),
    path("academics_classrooms/<int:pk>/edit/", views.AcademicsClassroomsUpdateView.as_view(), name="academics_classrooms_update"),
    path("academics_classrooms/<int:pk>/delete/", views.AcademicsClassroomsDeleteView.as_view(), name="academics_classrooms_delete"),
    path("academics_classrooms/<int:pk>/print/", views.AcademicsClassroomsPrintView.as_view(), name="academics_classrooms_print"),
    path("academics_classrooms/analytics/", views.AcademicsClassroomsAnalyticsView.as_view(), name="academics_classrooms_analytics"),
    path("academics_classrooms/export/csv/", views.export_academics_classrooms_csv, name="academics_classrooms_export_csv"),
    path("academics_classrooms/export/json/", views.export_academics_classrooms_json, name="academics_classrooms_export_json"),
]
