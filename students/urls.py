"""
URL Routes for Students: Student Lifecycle
"""

from django.urls import path
from students import views_students_lifecycle as views

app_name = "students"

urlpatterns = [
    path("students_lifecycle/", views.StudentsLifecycleListView.as_view(), name="students_lifecycle_list"),
    path("students_lifecycle/<int:pk>/", views.StudentsLifecycleDetailView.as_view(), name="students_lifecycle_detail"),
    path("students_lifecycle/create/", views.StudentsLifecycleCreateView.as_view(), name="students_lifecycle_create"),
    path("students_lifecycle/<int:pk>/edit/", views.StudentsLifecycleUpdateView.as_view(), name="students_lifecycle_update"),
    path("students_lifecycle/<int:pk>/delete/", views.StudentsLifecycleDeleteView.as_view(), name="students_lifecycle_delete"),
    path("students_lifecycle/<int:pk>/print/", views.StudentsLifecyclePrintView.as_view(), name="students_lifecycle_print"),
    path("students_lifecycle/analytics/", views.StudentsLifecycleAnalyticsView.as_view(), name="students_lifecycle_analytics"),
    path("students_lifecycle/export/csv/", views.export_students_lifecycle_csv, name="students_lifecycle_export_csv"),
    path("students_lifecycle/export/json/", views.export_students_lifecycle_json, name="students_lifecycle_export_json"),
]
