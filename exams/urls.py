"""
URL Routes for Exams: Invigilation Roster
"""

from django.urls import path
from exams import views_exams_invigilation as views

app_name = "exams"

urlpatterns = [
    path("exams_invigilation/", views.ExamsInvigilationListView.as_view(), name="exams_invigilation_list"),
    path("exams_invigilation/<int:pk>/", views.ExamsInvigilationDetailView.as_view(), name="exams_invigilation_detail"),
    path("exams_invigilation/create/", views.ExamsInvigilationCreateView.as_view(), name="exams_invigilation_create"),
    path("exams_invigilation/<int:pk>/edit/", views.ExamsInvigilationUpdateView.as_view(), name="exams_invigilation_update"),
    path("exams_invigilation/<int:pk>/delete/", views.ExamsInvigilationDeleteView.as_view(), name="exams_invigilation_delete"),
    path("exams_invigilation/<int:pk>/print/", views.ExamsInvigilationPrintView.as_view(), name="exams_invigilation_print"),
    path("exams_invigilation/analytics/", views.ExamsInvigilationAnalyticsView.as_view(), name="exams_invigilation_analytics"),
    path("exams_invigilation/export/csv/", views.export_exams_invigilation_csv, name="exams_invigilation_export_csv"),
    path("exams_invigilation/export/json/", views.export_exams_invigilation_json, name="exams_invigilation_export_json"),
]
