"""
URL Routes for Accounts: MFA & Security
"""

from django.urls import path
from accounts import views_accounts_mfa_security as views

app_name = "accounts"

urlpatterns = [
    path("accounts_mfa_security/", views.AccountsMfaSecurityListView.as_view(), name="accounts_mfa_security_list"),
    path("accounts_mfa_security/<int:pk>/", views.AccountsMfaSecurityDetailView.as_view(), name="accounts_mfa_security_detail"),
    path("accounts_mfa_security/create/", views.AccountsMfaSecurityCreateView.as_view(), name="accounts_mfa_security_create"),
    path("accounts_mfa_security/<int:pk>/edit/", views.AccountsMfaSecurityUpdateView.as_view(), name="accounts_mfa_security_update"),
    path("accounts_mfa_security/<int:pk>/delete/", views.AccountsMfaSecurityDeleteView.as_view(), name="accounts_mfa_security_delete"),
    path("accounts_mfa_security/<int:pk>/print/", views.AccountsMfaSecurityPrintView.as_view(), name="accounts_mfa_security_print"),
    path("accounts_mfa_security/analytics/", views.AccountsMfaSecurityAnalyticsView.as_view(), name="accounts_mfa_security_analytics"),
    path("accounts_mfa_security/export/csv/", views.export_accounts_mfa_security_csv, name="accounts_mfa_security_export_csv"),
    path("accounts_mfa_security/export/json/", views.export_accounts_mfa_security_json, name="accounts_mfa_security_export_json"),
]
