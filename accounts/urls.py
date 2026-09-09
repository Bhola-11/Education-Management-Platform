"""
URL Routes for Accounts: User Profiles
"""

from django.urls import path
from accounts import views_accounts_profiles as views

app_name = "accounts"

urlpatterns = [
    path("accounts_profiles/", views.AccountsProfilesListView.as_view(), name="accounts_profiles_list"),
    path("accounts_profiles/<int:pk>/", views.AccountsProfilesDetailView.as_view(), name="accounts_profiles_detail"),
    path("accounts_profiles/create/", views.AccountsProfilesCreateView.as_view(), name="accounts_profiles_create"),
    path("accounts_profiles/<int:pk>/edit/", views.AccountsProfilesUpdateView.as_view(), name="accounts_profiles_update"),
    path("accounts_profiles/<int:pk>/delete/", views.AccountsProfilesDeleteView.as_view(), name="accounts_profiles_delete"),
    path("accounts_profiles/<int:pk>/print/", views.AccountsProfilesPrintView.as_view(), name="accounts_profiles_print"),
    path("accounts_profiles/analytics/", views.AccountsProfilesAnalyticsView.as_view(), name="accounts_profiles_analytics"),
    path("accounts_profiles/export/csv/", views.export_accounts_profiles_csv, name="accounts_profiles_export_csv"),
    path("accounts_profiles/export/json/", views.export_accounts_profiles_json, name="accounts_profiles_export_json"),
]
