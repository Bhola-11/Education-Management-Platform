"""
URL Routes for Exams: Exam Scheduling
"""

from django.urls import path
from exams import views_exams_schedules as views

app_name = "exams"

urlpatterns = [
    path("exams_schedules/", views.ExamsSchedulesListView.as_view(), name="exams_schedules_list"),
    path("exams_schedules/<int:pk>/", views.ExamsSchedulesDetailView.as_view(), name="exams_schedules_detail"),
    path("exams_schedules/create/", views.ExamsSchedulesCreateView.as_view(), name="exams_schedules_create"),
    path("exams_schedules/<int:pk>/edit/", views.ExamsSchedulesUpdateView.as_view(), name="exams_schedules_update"),
    path("exams_schedules/<int:pk>/delete/", views.ExamsSchedulesDeleteView.as_view(), name="exams_schedules_delete"),
    path("exams_schedules/<int:pk>/print/", views.ExamsSchedulesPrintView.as_view(), name="exams_schedules_print"),
    path("exams_schedules/analytics/", views.ExamsSchedulesAnalyticsView.as_view(), name="exams_schedules_analytics"),
    path("exams_schedules/export/csv/", views.export_exams_schedules_csv, name="exams_schedules_export_csv"),
    path("exams_schedules/export/json/", views.export_exams_schedules_json, name="exams_schedules_export_json"),
]
