"""
URL Routes for Accounts: Authentication Views
"""

from django.urls import path
from accounts import views_accounts_auth_views as views

app_name = "accounts"

urlpatterns = [
    path("accounts_auth_views/", views.AccountsAuthViewsListView.as_view(), name="accounts_auth_views_list"),
    path("accounts_auth_views/<int:pk>/", views.AccountsAuthViewsDetailView.as_view(), name="accounts_auth_views_detail"),
    path("accounts_auth_views/create/", views.AccountsAuthViewsCreateView.as_view(), name="accounts_auth_views_create"),
    path("accounts_auth_views/<int:pk>/edit/", views.AccountsAuthViewsUpdateView.as_view(), name="accounts_auth_views_update"),
    path("accounts_auth_views/<int:pk>/delete/", views.AccountsAuthViewsDeleteView.as_view(), name="accounts_auth_views_delete"),
    path("accounts_auth_views/<int:pk>/print/", views.AccountsAuthViewsPrintView.as_view(), name="accounts_auth_views_print"),
    path("accounts_auth_views/analytics/", views.AccountsAuthViewsAnalyticsView.as_view(), name="accounts_auth_views_analytics"),
    path("accounts_auth_views/export/csv/", views.export_accounts_auth_views_csv, name="accounts_auth_views_export_csv"),
    path("accounts_auth_views/export/json/", views.export_accounts_auth_views_json, name="accounts_auth_views_export_json"),
]
