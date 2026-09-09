"""
URL Routes for Enrollment: Application Decisioning
"""

from django.urls import path
from enrollment import views_enrollment_review as views

app_name = "enrollment"

urlpatterns = [
    path("enrollment_review/", views.EnrollmentReviewListView.as_view(), name="enrollment_review_list"),
    path("enrollment_review/<int:pk>/", views.EnrollmentReviewDetailView.as_view(), name="enrollment_review_detail"),
    path("enrollment_review/create/", views.EnrollmentReviewCreateView.as_view(), name="enrollment_review_create"),
    path("enrollment_review/<int:pk>/edit/", views.EnrollmentReviewUpdateView.as_view(), name="enrollment_review_update"),
    path("enrollment_review/<int:pk>/delete/", views.EnrollmentReviewDeleteView.as_view(), name="enrollment_review_delete"),
    path("enrollment_review/<int:pk>/print/", views.EnrollmentReviewPrintView.as_view(), name="enrollment_review_print"),
    path("enrollment_review/analytics/", views.EnrollmentReviewAnalyticsView.as_view(), name="enrollment_review_analytics"),
    path("enrollment_review/export/csv/", views.export_enrollment_review_csv, name="enrollment_review_export_csv"),
    path("enrollment_review/export/json/", views.export_enrollment_review_json, name="enrollment_review_export_json"),
]
