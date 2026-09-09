"""
URL Routes for Accounts: Accounts & Academics Tests
"""

from django.urls import path
from accounts import views_accounts_and_academics_suite as views

app_name = "accounts"

urlpatterns = [
    path("accounts_and_academics_suite/", views.AccountsAndAcademicsSuiteListView.as_view(), name="accounts_and_academics_suite_list"),
    path("accounts_and_academics_suite/<int:pk>/", views.AccountsAndAcademicsSuiteDetailView.as_view(), name="accounts_and_academics_suite_detail"),
    path("accounts_and_academics_suite/create/", views.AccountsAndAcademicsSuiteCreateView.as_view(), name="accounts_and_academics_suite_create"),
    path("accounts_and_academics_suite/<int:pk>/edit/", views.AccountsAndAcademicsSuiteUpdateView.as_view(), name="accounts_and_academics_suite_update"),
    path("accounts_and_academics_suite/<int:pk>/delete/", views.AccountsAndAcademicsSuiteDeleteView.as_view(), name="accounts_and_academics_suite_delete"),
    path("accounts_and_academics_suite/<int:pk>/print/", views.AccountsAndAcademicsSuitePrintView.as_view(), name="accounts_and_academics_suite_print"),
    path("accounts_and_academics_suite/analytics/", views.AccountsAndAcademicsSuiteAnalyticsView.as_view(), name="accounts_and_academics_suite_analytics"),
    path("accounts_and_academics_suite/export/csv/", views.export_accounts_and_academics_suite_csv, name="accounts_and_academics_suite_export_csv"),
    path("accounts_and_academics_suite/export/json/", views.export_accounts_and_academics_suite_json, name="accounts_and_academics_suite_export_json"),
]
