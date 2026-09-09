"""
URL Routes for Enrollment: Cohorts & Sections
"""

from django.urls import path
from enrollment import views_enrollment_cohorts as views

app_name = "enrollment"

urlpatterns = [
    path("enrollment_cohorts/", views.EnrollmentCohortsListView.as_view(), name="enrollment_cohorts_list"),
    path("enrollment_cohorts/<int:pk>/", views.EnrollmentCohortsDetailView.as_view(), name="enrollment_cohorts_detail"),
    path("enrollment_cohorts/create/", views.EnrollmentCohortsCreateView.as_view(), name="enrollment_cohorts_create"),
    path("enrollment_cohorts/<int:pk>/edit/", views.EnrollmentCohortsUpdateView.as_view(), name="enrollment_cohorts_update"),
    path("enrollment_cohorts/<int:pk>/delete/", views.EnrollmentCohortsDeleteView.as_view(), name="enrollment_cohorts_delete"),
    path("enrollment_cohorts/<int:pk>/print/", views.EnrollmentCohortsPrintView.as_view(), name="enrollment_cohorts_print"),
    path("enrollment_cohorts/analytics/", views.EnrollmentCohortsAnalyticsView.as_view(), name="enrollment_cohorts_analytics"),
    path("enrollment_cohorts/export/csv/", views.export_enrollment_cohorts_csv, name="enrollment_cohorts_export_csv"),
    path("enrollment_cohorts/export/json/", views.export_enrollment_cohorts_json, name="enrollment_cohorts_export_json"),
]
