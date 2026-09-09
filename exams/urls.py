"""
URL Routes for Exams: Exam Cycles & Series
"""

from django.urls import path
from exams import views_exams_periods as views

app_name = "exams"

urlpatterns = [
    path("exams_periods/", views.ExamsPeriodsListView.as_view(), name="exams_periods_list"),
    path("exams_periods/<int:pk>/", views.ExamsPeriodsDetailView.as_view(), name="exams_periods_detail"),
    path("exams_periods/create/", views.ExamsPeriodsCreateView.as_view(), name="exams_periods_create"),
    path("exams_periods/<int:pk>/edit/", views.ExamsPeriodsUpdateView.as_view(), name="exams_periods_update"),
    path("exams_periods/<int:pk>/delete/", views.ExamsPeriodsDeleteView.as_view(), name="exams_periods_delete"),
    path("exams_periods/<int:pk>/print/", views.ExamsPeriodsPrintView.as_view(), name="exams_periods_print"),
    path("exams_periods/analytics/", views.ExamsPeriodsAnalyticsView.as_view(), name="exams_periods_analytics"),
    path("exams_periods/export/csv/", views.export_exams_periods_csv, name="exams_periods_export_csv"),
    path("exams_periods/export/json/", views.export_exams_periods_json, name="exams_periods_export_json"),
]
