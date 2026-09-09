"""
URL Routes for Analytics: Student Retention Analytics
"""

from django.urls import path
from analytics import views_analytics_student_progression as views

app_name = "analytics"

urlpatterns = [
    path("analytics_student_progression/", views.AnalyticsStudentProgressionListView.as_view(), name="analytics_student_progression_list"),
    path("analytics_student_progression/<int:pk>/", views.AnalyticsStudentProgressionDetailView.as_view(), name="analytics_student_progression_detail"),
    path("analytics_student_progression/create/", views.AnalyticsStudentProgressionCreateView.as_view(), name="analytics_student_progression_create"),
    path("analytics_student_progression/<int:pk>/edit/", views.AnalyticsStudentProgressionUpdateView.as_view(), name="analytics_student_progression_update"),
    path("analytics_student_progression/<int:pk>/delete/", views.AnalyticsStudentProgressionDeleteView.as_view(), name="analytics_student_progression_delete"),
    path("analytics_student_progression/<int:pk>/print/", views.AnalyticsStudentProgressionPrintView.as_view(), name="analytics_student_progression_print"),
    path("analytics_student_progression/analytics/", views.AnalyticsStudentProgressionAnalyticsView.as_view(), name="analytics_student_progression_analytics"),
    path("analytics_student_progression/export/csv/", views.export_analytics_student_progression_csv, name="analytics_student_progression_export_csv"),
    path("analytics_student_progression/export/json/", views.export_analytics_student_progression_json, name="analytics_student_progression_export_json"),
]
