"""
URL Routes for Students: Guardians & Parents
"""

from django.urls import path
from students import views_students_guardians as views

app_name = "students"

urlpatterns = [
    path("students_guardians/", views.StudentsGuardiansListView.as_view(), name="students_guardians_list"),
    path("students_guardians/<int:pk>/", views.StudentsGuardiansDetailView.as_view(), name="students_guardians_detail"),
    path("students_guardians/create/", views.StudentsGuardiansCreateView.as_view(), name="students_guardians_create"),
    path("students_guardians/<int:pk>/edit/", views.StudentsGuardiansUpdateView.as_view(), name="students_guardians_update"),
    path("students_guardians/<int:pk>/delete/", views.StudentsGuardiansDeleteView.as_view(), name="students_guardians_delete"),
    path("students_guardians/<int:pk>/print/", views.StudentsGuardiansPrintView.as_view(), name="students_guardians_print"),
    path("students_guardians/analytics/", views.StudentsGuardiansAnalyticsView.as_view(), name="students_guardians_analytics"),
    path("students_guardians/export/csv/", views.export_students_guardians_csv, name="students_guardians_export_csv"),
    path("students_guardians/export/json/", views.export_students_guardians_json, name="students_guardians_export_json"),
]
