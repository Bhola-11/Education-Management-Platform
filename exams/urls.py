"""
URL Routes for Exams: Exam Seating Matrix
"""

from django.urls import path
from exams import views_exams_hall_seating as views

app_name = "exams"

urlpatterns = [
    path("exams_hall_seating/", views.ExamsHallSeatingListView.as_view(), name="exams_hall_seating_list"),
    path("exams_hall_seating/<int:pk>/", views.ExamsHallSeatingDetailView.as_view(), name="exams_hall_seating_detail"),
    path("exams_hall_seating/create/", views.ExamsHallSeatingCreateView.as_view(), name="exams_hall_seating_create"),
    path("exams_hall_seating/<int:pk>/edit/", views.ExamsHallSeatingUpdateView.as_view(), name="exams_hall_seating_update"),
    path("exams_hall_seating/<int:pk>/delete/", views.ExamsHallSeatingDeleteView.as_view(), name="exams_hall_seating_delete"),
    path("exams_hall_seating/<int:pk>/print/", views.ExamsHallSeatingPrintView.as_view(), name="exams_hall_seating_print"),
    path("exams_hall_seating/analytics/", views.ExamsHallSeatingAnalyticsView.as_view(), name="exams_hall_seating_analytics"),
    path("exams_hall_seating/export/csv/", views.export_exams_hall_seating_csv, name="exams_hall_seating_export_csv"),
    path("exams_hall_seating/export/json/", views.export_exams_hall_seating_json, name="exams_hall_seating_export_json"),
]
