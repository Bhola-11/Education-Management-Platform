"""
URL Routes for Fees: Scholarships & Waivers
"""

from django.urls import path
from fees import views_fees_scholarships as views

app_name = "fees"

urlpatterns = [
    path("fees_scholarships/", views.FeesScholarshipsListView.as_view(), name="fees_scholarships_list"),
    path("fees_scholarships/<int:pk>/", views.FeesScholarshipsDetailView.as_view(), name="fees_scholarships_detail"),
    path("fees_scholarships/create/", views.FeesScholarshipsCreateView.as_view(), name="fees_scholarships_create"),
    path("fees_scholarships/<int:pk>/edit/", views.FeesScholarshipsUpdateView.as_view(), name="fees_scholarships_update"),
    path("fees_scholarships/<int:pk>/delete/", views.FeesScholarshipsDeleteView.as_view(), name="fees_scholarships_delete"),
    path("fees_scholarships/<int:pk>/print/", views.FeesScholarshipsPrintView.as_view(), name="fees_scholarships_print"),
    path("fees_scholarships/analytics/", views.FeesScholarshipsAnalyticsView.as_view(), name="fees_scholarships_analytics"),
    path("fees_scholarships/export/csv/", views.export_fees_scholarships_csv, name="fees_scholarships_export_csv"),
    path("fees_scholarships/export/json/", views.export_fees_scholarships_json, name="fees_scholarships_export_json"),
]
