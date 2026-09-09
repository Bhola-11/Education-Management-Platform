"""
URL Routes for Accounts: Role-Based Access Control
"""

from django.urls import path
from accounts import views_accounts_roles_rbac as views

app_name = "accounts"

urlpatterns = [
    path("accounts_roles_rbac/", views.AccountsRolesRbacListView.as_view(), name="accounts_roles_rbac_list"),
    path("accounts_roles_rbac/<int:pk>/", views.AccountsRolesRbacDetailView.as_view(), name="accounts_roles_rbac_detail"),
    path("accounts_roles_rbac/create/", views.AccountsRolesRbacCreateView.as_view(), name="accounts_roles_rbac_create"),
    path("accounts_roles_rbac/<int:pk>/edit/", views.AccountsRolesRbacUpdateView.as_view(), name="accounts_roles_rbac_update"),
    path("accounts_roles_rbac/<int:pk>/delete/", views.AccountsRolesRbacDeleteView.as_view(), name="accounts_roles_rbac_delete"),
    path("accounts_roles_rbac/<int:pk>/print/", views.AccountsRolesRbacPrintView.as_view(), name="accounts_roles_rbac_print"),
    path("accounts_roles_rbac/analytics/", views.AccountsRolesRbacAnalyticsView.as_view(), name="accounts_roles_rbac_analytics"),
    path("accounts_roles_rbac/export/csv/", views.export_accounts_roles_rbac_csv, name="accounts_roles_rbac_export_csv"),
    path("accounts_roles_rbac/export/json/", views.export_accounts_roles_rbac_json, name="accounts_roles_rbac_export_json"),
]
