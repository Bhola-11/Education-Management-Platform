"""
URL Routes for Academics: Course Catalog
"""

from django.urls import path
from academics import views_academics_courses as views

app_name = "academics"

urlpatterns = [
    path("academics_courses/", views.AcademicsCoursesListView.as_view(), name="academics_courses_list"),
    path("academics_courses/<int:pk>/", views.AcademicsCoursesDetailView.as_view(), name="academics_courses_detail"),
    path("academics_courses/create/", views.AcademicsCoursesCreateView.as_view(), name="academics_courses_create"),
    path("academics_courses/<int:pk>/edit/", views.AcademicsCoursesUpdateView.as_view(), name="academics_courses_update"),
    path("academics_courses/<int:pk>/delete/", views.AcademicsCoursesDeleteView.as_view(), name="academics_courses_delete"),
    path("academics_courses/<int:pk>/print/", views.AcademicsCoursesPrintView.as_view(), name="academics_courses_print"),
    path("academics_courses/analytics/", views.AcademicsCoursesAnalyticsView.as_view(), name="academics_courses_analytics"),
    path("academics_courses/export/csv/", views.export_academics_courses_csv, name="academics_courses_export_csv"),
    path("academics_courses/export/json/", views.export_academics_courses_json, name="academics_courses_export_json"),
]
