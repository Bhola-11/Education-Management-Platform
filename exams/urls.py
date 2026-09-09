"""
URL Routes for Exams: Admit Cards & Hall Tickets
"""

from django.urls import path
from exams import views_exams_admit_cards as views

app_name = "exams"

urlpatterns = [
    path("exams_admit_cards/", views.ExamsAdmitCardsListView.as_view(), name="exams_admit_cards_list"),
    path("exams_admit_cards/<int:pk>/", views.ExamsAdmitCardsDetailView.as_view(), name="exams_admit_cards_detail"),
    path("exams_admit_cards/create/", views.ExamsAdmitCardsCreateView.as_view(), name="exams_admit_cards_create"),
    path("exams_admit_cards/<int:pk>/edit/", views.ExamsAdmitCardsUpdateView.as_view(), name="exams_admit_cards_update"),
    path("exams_admit_cards/<int:pk>/delete/", views.ExamsAdmitCardsDeleteView.as_view(), name="exams_admit_cards_delete"),
    path("exams_admit_cards/<int:pk>/print/", views.ExamsAdmitCardsPrintView.as_view(), name="exams_admit_cards_print"),
    path("exams_admit_cards/analytics/", views.ExamsAdmitCardsAnalyticsView.as_view(), name="exams_admit_cards_analytics"),
    path("exams_admit_cards/export/csv/", views.export_exams_admit_cards_csv, name="exams_admit_cards_export_csv"),
    path("exams_admit_cards/export/json/", views.export_exams_admit_cards_json, name="exams_admit_cards_export_json"),
]
