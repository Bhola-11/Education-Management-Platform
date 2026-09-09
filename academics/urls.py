"""
URL Routes for Academics: Departments & Faculties
"""

from django.urls import path
from academics import views_academics_departments as views

app_name = "academics"

urlpatterns = [
    path("academics_departments/", views.AcademicsDepartmentsListView.as_view(), name="academics_departments_list"),
    path("academics_departments/<int:pk>/", views.AcademicsDepartmentsDetailView.as_view(), name="academics_departments_detail"),
    path("academics_departments/create/", views.AcademicsDepartmentsCreateView.as_view(), name="academics_departments_create"),
    path("academics_departments/<int:pk>/edit/", views.AcademicsDepartmentsUpdateView.as_view(), name="academics_departments_update"),
    path("academics_departments/<int:pk>/delete/", views.AcademicsDepartmentsDeleteView.as_view(), name="academics_departments_delete"),
    path("academics_departments/<int:pk>/print/", views.AcademicsDepartmentsPrintView.as_view(), name="academics_departments_print"),
    path("academics_departments/analytics/", views.AcademicsDepartmentsAnalyticsView.as_view(), name="academics_departments_analytics"),
    path("academics_departments/export/csv/", views.export_academics_departments_csv, name="academics_departments_export_csv"),
    path("academics_departments/export/json/", views.export_academics_departments_json, name="academics_departments_export_json"),
]
