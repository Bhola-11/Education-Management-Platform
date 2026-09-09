"""
URL Routes for Analytics: Attendance Attrition Models
"""

from django.urls import path
from analytics import views_analytics_attendance_attrition as views

app_name = "analytics"

urlpatterns = [
    path("analytics_attendance_attrition/", views.AnalyticsAttendanceAttritionListView.as_view(), name="analytics_attendance_attrition_list"),
    path("analytics_attendance_attrition/<int:pk>/", views.AnalyticsAttendanceAttritionDetailView.as_view(), name="analytics_attendance_attrition_detail"),
    path("analytics_attendance_attrition/create/", views.AnalyticsAttendanceAttritionCreateView.as_view(), name="analytics_attendance_attrition_create"),
    path("analytics_attendance_attrition/<int:pk>/edit/", views.AnalyticsAttendanceAttritionUpdateView.as_view(), name="analytics_attendance_attrition_update"),
    path("analytics_attendance_attrition/<int:pk>/delete/", views.AnalyticsAttendanceAttritionDeleteView.as_view(), name="analytics_attendance_attrition_delete"),
    path("analytics_attendance_attrition/<int:pk>/print/", views.AnalyticsAttendanceAttritionPrintView.as_view(), name="analytics_attendance_attrition_print"),
    path("analytics_attendance_attrition/analytics/", views.AnalyticsAttendanceAttritionAnalyticsView.as_view(), name="analytics_attendance_attrition_analytics"),
    path("analytics_attendance_attrition/export/csv/", views.export_analytics_attendance_attrition_csv, name="analytics_attendance_attrition_export_csv"),
    path("analytics_attendance_attrition/export/json/", views.export_analytics_attendance_attrition_json, name="analytics_attendance_attrition_export_json"),
]
