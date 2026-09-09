"""
URL Routes for Core: Institutional Settings
"""

from django.urls import path
from core import views_core_system_settings as views

app_name = "core"

urlpatterns = [
    path("core_system_settings/", views.CoreSystemSettingsListView.as_view(), name="core_system_settings_list"),
    path("core_system_settings/<int:pk>/", views.CoreSystemSettingsDetailView.as_view(), name="core_system_settings_detail"),
    path("core_system_settings/create/", views.CoreSystemSettingsCreateView.as_view(), name="core_system_settings_create"),
    path("core_system_settings/<int:pk>/edit/", views.CoreSystemSettingsUpdateView.as_view(), name="core_system_settings_update"),
    path("core_system_settings/<int:pk>/delete/", views.CoreSystemSettingsDeleteView.as_view(), name="core_system_settings_delete"),
    path("core_system_settings/<int:pk>/print/", views.CoreSystemSettingsPrintView.as_view(), name="core_system_settings_print"),
    path("core_system_settings/analytics/", views.CoreSystemSettingsAnalyticsView.as_view(), name="core_system_settings_analytics"),
    path("core_system_settings/export/csv/", views.export_core_system_settings_csv, name="core_system_settings_export_csv"),
    path("core_system_settings/export/json/", views.export_core_system_settings_json, name="core_system_settings_export_json"),
]
