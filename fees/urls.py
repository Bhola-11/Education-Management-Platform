"""
URL Routes for Fees: Late Fee Penalties
"""

from django.urls import path
from fees import views_fees_penalties as views

app_name = "fees"

urlpatterns = [
    path("fees_penalties/", views.FeesPenaltiesListView.as_view(), name="fees_penalties_list"),
    path("fees_penalties/<int:pk>/", views.FeesPenaltiesDetailView.as_view(), name="fees_penalties_detail"),
    path("fees_penalties/create/", views.FeesPenaltiesCreateView.as_view(), name="fees_penalties_create"),
    path("fees_penalties/<int:pk>/edit/", views.FeesPenaltiesUpdateView.as_view(), name="fees_penalties_update"),
    path("fees_penalties/<int:pk>/delete/", views.FeesPenaltiesDeleteView.as_view(), name="fees_penalties_delete"),
    path("fees_penalties/<int:pk>/print/", views.FeesPenaltiesPrintView.as_view(), name="fees_penalties_print"),
    path("fees_penalties/analytics/", views.FeesPenaltiesAnalyticsView.as_view(), name="fees_penalties_analytics"),
    path("fees_penalties/export/csv/", views.export_fees_penalties_csv, name="fees_penalties_export_csv"),
    path("fees_penalties/export/json/", views.export_fees_penalties_json, name="fees_penalties_export_json"),
]
