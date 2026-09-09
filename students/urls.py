"""
URL Routes for Students: Student Demographics
"""

from django.urls import path
from students import views_students_demographics as views

app_name = "students"

urlpatterns = [
    path("students_demographics/", views.StudentsDemographicsListView.as_view(), name="students_demographics_list"),
    path("students_demographics/<int:pk>/", views.StudentsDemographicsDetailView.as_view(), name="students_demographics_detail"),
    path("students_demographics/create/", views.StudentsDemographicsCreateView.as_view(), name="students_demographics_create"),
    path("students_demographics/<int:pk>/edit/", views.StudentsDemographicsUpdateView.as_view(), name="students_demographics_update"),
    path("students_demographics/<int:pk>/delete/", views.StudentsDemographicsDeleteView.as_view(), name="students_demographics_delete"),
    path("students_demographics/<int:pk>/print/", views.StudentsDemographicsPrintView.as_view(), name="students_demographics_print"),
    path("students_demographics/analytics/", views.StudentsDemographicsAnalyticsView.as_view(), name="students_demographics_analytics"),
    path("students_demographics/export/csv/", views.export_students_demographics_csv, name="students_demographics_export_csv"),
    path("students_demographics/export/json/", views.export_students_demographics_json, name="students_demographics_export_json"),
]
