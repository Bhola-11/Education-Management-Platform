"""
URL Routes for Teachers: Department Affiliations
"""

from django.urls import path
from teachers import views_teachers_departments as views

app_name = "teachers"

urlpatterns = [
    path("teachers_departments/", views.TeachersDepartmentsListView.as_view(), name="teachers_departments_list"),
    path("teachers_departments/<int:pk>/", views.TeachersDepartmentsDetailView.as_view(), name="teachers_departments_detail"),
    path("teachers_departments/create/", views.TeachersDepartmentsCreateView.as_view(), name="teachers_departments_create"),
    path("teachers_departments/<int:pk>/edit/", views.TeachersDepartmentsUpdateView.as_view(), name="teachers_departments_update"),
    path("teachers_departments/<int:pk>/delete/", views.TeachersDepartmentsDeleteView.as_view(), name="teachers_departments_delete"),
    path("teachers_departments/<int:pk>/print/", views.TeachersDepartmentsPrintView.as_view(), name="teachers_departments_print"),
    path("teachers_departments/analytics/", views.TeachersDepartmentsAnalyticsView.as_view(), name="teachers_departments_analytics"),
    path("teachers_departments/export/csv/", views.export_teachers_departments_csv, name="teachers_departments_export_csv"),
    path("teachers_departments/export/json/", views.export_teachers_departments_json, name="teachers_departments_export_json"),
]
