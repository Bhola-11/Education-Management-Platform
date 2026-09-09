"""
URL Routes for Core: Security & Penetration Tests
"""

from django.urls import path
from core import views_security_and_permissions_suite as views

app_name = "core"

urlpatterns = [
    path("security_and_permissions_suite/", views.SecurityAndPermissionsSuiteListView.as_view(), name="security_and_permissions_suite_list"),
    path("security_and_permissions_suite/<int:pk>/", views.SecurityAndPermissionsSuiteDetailView.as_view(), name="security_and_permissions_suite_detail"),
    path("security_and_permissions_suite/create/", views.SecurityAndPermissionsSuiteCreateView.as_view(), name="security_and_permissions_suite_create"),
    path("security_and_permissions_suite/<int:pk>/edit/", views.SecurityAndPermissionsSuiteUpdateView.as_view(), name="security_and_permissions_suite_update"),
    path("security_and_permissions_suite/<int:pk>/delete/", views.SecurityAndPermissionsSuiteDeleteView.as_view(), name="security_and_permissions_suite_delete"),
    path("security_and_permissions_suite/<int:pk>/print/", views.SecurityAndPermissionsSuitePrintView.as_view(), name="security_and_permissions_suite_print"),
    path("security_and_permissions_suite/analytics/", views.SecurityAndPermissionsSuiteAnalyticsView.as_view(), name="security_and_permissions_suite_analytics"),
    path("security_and_permissions_suite/export/csv/", views.export_security_and_permissions_suite_csv, name="security_and_permissions_suite_export_csv"),
    path("security_and_permissions_suite/export/json/", views.export_security_and_permissions_suite_json, name="security_and_permissions_suite_export_json"),
]
