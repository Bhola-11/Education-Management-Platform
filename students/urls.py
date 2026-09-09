"""
URL Routes for Students: Student Health & Safety
"""

from django.urls import path
from students import views_students_emergency_health as views

app_name = "students"

urlpatterns = [
    path("students_emergency_health/", views.StudentsEmergencyHealthListView.as_view(), name="students_emergency_health_list"),
    path("students_emergency_health/<int:pk>/", views.StudentsEmergencyHealthDetailView.as_view(), name="students_emergency_health_detail"),
    path("students_emergency_health/create/", views.StudentsEmergencyHealthCreateView.as_view(), name="students_emergency_health_create"),
    path("students_emergency_health/<int:pk>/edit/", views.StudentsEmergencyHealthUpdateView.as_view(), name="students_emergency_health_update"),
    path("students_emergency_health/<int:pk>/delete/", views.StudentsEmergencyHealthDeleteView.as_view(), name="students_emergency_health_delete"),
    path("students_emergency_health/<int:pk>/print/", views.StudentsEmergencyHealthPrintView.as_view(), name="students_emergency_health_print"),
    path("students_emergency_health/analytics/", views.StudentsEmergencyHealthAnalyticsView.as_view(), name="students_emergency_health_analytics"),
    path("students_emergency_health/export/csv/", views.export_students_emergency_health_csv, name="students_emergency_health_export_csv"),
    path("students_emergency_health/export/json/", views.export_students_emergency_health_json, name="students_emergency_health_export_json"),
]
