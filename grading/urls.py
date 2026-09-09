"""
URL Routes for Grading: Grading & Fees Tests
"""

from django.urls import path
from grading import views_grading_and_fees_suite as views

app_name = "grading"

urlpatterns = [
    path("grading_and_fees_suite/", views.GradingAndFeesSuiteListView.as_view(), name="grading_and_fees_suite_list"),
    path("grading_and_fees_suite/<int:pk>/", views.GradingAndFeesSuiteDetailView.as_view(), name="grading_and_fees_suite_detail"),
    path("grading_and_fees_suite/create/", views.GradingAndFeesSuiteCreateView.as_view(), name="grading_and_fees_suite_create"),
    path("grading_and_fees_suite/<int:pk>/edit/", views.GradingAndFeesSuiteUpdateView.as_view(), name="grading_and_fees_suite_update"),
    path("grading_and_fees_suite/<int:pk>/delete/", views.GradingAndFeesSuiteDeleteView.as_view(), name="grading_and_fees_suite_delete"),
    path("grading_and_fees_suite/<int:pk>/print/", views.GradingAndFeesSuitePrintView.as_view(), name="grading_and_fees_suite_print"),
    path("grading_and_fees_suite/analytics/", views.GradingAndFeesSuiteAnalyticsView.as_view(), name="grading_and_fees_suite_analytics"),
    path("grading_and_fees_suite/export/csv/", views.export_grading_and_fees_suite_csv, name="grading_and_fees_suite_export_csv"),
    path("grading_and_fees_suite/export/json/", views.export_grading_and_fees_suite_json, name="grading_and_fees_suite_export_json"),
]
