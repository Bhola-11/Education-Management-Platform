"""
URL Routes for Fees: Fee Structures & Pricing
"""

from django.urls import path
from fees import views_fees_structures as views

app_name = "fees"

urlpatterns = [
    path("fees_structures/", views.FeesStructuresListView.as_view(), name="fees_structures_list"),
    path("fees_structures/<int:pk>/", views.FeesStructuresDetailView.as_view(), name="fees_structures_detail"),
    path("fees_structures/create/", views.FeesStructuresCreateView.as_view(), name="fees_structures_create"),
    path("fees_structures/<int:pk>/edit/", views.FeesStructuresUpdateView.as_view(), name="fees_structures_update"),
    path("fees_structures/<int:pk>/delete/", views.FeesStructuresDeleteView.as_view(), name="fees_structures_delete"),
    path("fees_structures/<int:pk>/print/", views.FeesStructuresPrintView.as_view(), name="fees_structures_print"),
    path("fees_structures/analytics/", views.FeesStructuresAnalyticsView.as_view(), name="fees_structures_analytics"),
    path("fees_structures/export/csv/", views.export_fees_structures_csv, name="fees_structures_export_csv"),
    path("fees_structures/export/json/", views.export_fees_structures_json, name="fees_structures_export_json"),
]
