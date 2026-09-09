"""
URL Routes for Academics: Academic Calendar
"""

from django.urls import path
from academics import views_academics_calendar as views

app_name = "academics"

urlpatterns = [
    path("academics_calendar/", views.AcademicsCalendarListView.as_view(), name="academics_calendar_list"),
    path("academics_calendar/<int:pk>/", views.AcademicsCalendarDetailView.as_view(), name="academics_calendar_detail"),
    path("academics_calendar/create/", views.AcademicsCalendarCreateView.as_view(), name="academics_calendar_create"),
    path("academics_calendar/<int:pk>/edit/", views.AcademicsCalendarUpdateView.as_view(), name="academics_calendar_update"),
    path("academics_calendar/<int:pk>/delete/", views.AcademicsCalendarDeleteView.as_view(), name="academics_calendar_delete"),
    path("academics_calendar/<int:pk>/print/", views.AcademicsCalendarPrintView.as_view(), name="academics_calendar_print"),
    path("academics_calendar/analytics/", views.AcademicsCalendarAnalyticsView.as_view(), name="academics_calendar_analytics"),
    path("academics_calendar/export/csv/", views.export_academics_calendar_csv, name="academics_calendar_export_csv"),
    path("academics_calendar/export/json/", views.export_academics_calendar_json, name="academics_calendar_export_json"),
]
