"""
URL Routes for Accounts: Authentication
"""

from django.urls import path
from accounts import views_accounts_custom_user as views

app_name = "accounts"

urlpatterns = [
    path("accounts_custom_user/", views.AccountsCustomUserListView.as_view(), name="accounts_custom_user_list"),
    path("accounts_custom_user/<int:pk>/", views.AccountsCustomUserDetailView.as_view(), name="accounts_custom_user_detail"),
    path("accounts_custom_user/create/", views.AccountsCustomUserCreateView.as_view(), name="accounts_custom_user_create"),
    path("accounts_custom_user/<int:pk>/edit/", views.AccountsCustomUserUpdateView.as_view(), name="accounts_custom_user_update"),
    path("accounts_custom_user/<int:pk>/delete/", views.AccountsCustomUserDeleteView.as_view(), name="accounts_custom_user_delete"),
    path("accounts_custom_user/<int:pk>/print/", views.AccountsCustomUserPrintView.as_view(), name="accounts_custom_user_print"),
    path("accounts_custom_user/analytics/", views.AccountsCustomUserAnalyticsView.as_view(), name="accounts_custom_user_analytics"),
    path("accounts_custom_user/export/csv/", views.export_accounts_custom_user_csv, name="accounts_custom_user_export_csv"),
    path("accounts_custom_user/export/json/", views.export_accounts_custom_user_json, name="accounts_custom_user_export_json"),
]
