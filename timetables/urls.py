"""
URL Routes for Timetables: Faculty Substitutions
"""

from django.urls import path
from timetables import views_timetables_substitutions as views

app_name = "timetables"

urlpatterns = [
    path("timetables_substitutions/", views.TimetablesSubstitutionsListView.as_view(), name="timetables_substitutions_list"),
    path("timetables_substitutions/<int:pk>/", views.TimetablesSubstitutionsDetailView.as_view(), name="timetables_substitutions_detail"),
    path("timetables_substitutions/create/", views.TimetablesSubstitutionsCreateView.as_view(), name="timetables_substitutions_create"),
    path("timetables_substitutions/<int:pk>/edit/", views.TimetablesSubstitutionsUpdateView.as_view(), name="timetables_substitutions_update"),
    path("timetables_substitutions/<int:pk>/delete/", views.TimetablesSubstitutionsDeleteView.as_view(), name="timetables_substitutions_delete"),
    path("timetables_substitutions/<int:pk>/print/", views.TimetablesSubstitutionsPrintView.as_view(), name="timetables_substitutions_print"),
    path("timetables_substitutions/analytics/", views.TimetablesSubstitutionsAnalyticsView.as_view(), name="timetables_substitutions_analytics"),
    path("timetables_substitutions/export/csv/", views.export_timetables_substitutions_csv, name="timetables_substitutions_export_csv"),
    path("timetables_substitutions/export/json/", views.export_timetables_substitutions_json, name="timetables_substitutions_export_json"),
]
