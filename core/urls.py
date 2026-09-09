"""
URL Routes for Core: Database Diagnostics & Snapshots
"""

from django.urls import path
from core import views_core_backup_restore as views

app_name = "core"

urlpatterns = [
    path("core_backup_restore/", views.CoreBackupRestoreListView.as_view(), name="core_backup_restore_list"),
    path("core_backup_restore/<int:pk>/", views.CoreBackupRestoreDetailView.as_view(), name="core_backup_restore_detail"),
    path("core_backup_restore/create/", views.CoreBackupRestoreCreateView.as_view(), name="core_backup_restore_create"),
    path("core_backup_restore/<int:pk>/edit/", views.CoreBackupRestoreUpdateView.as_view(), name="core_backup_restore_update"),
    path("core_backup_restore/<int:pk>/delete/", views.CoreBackupRestoreDeleteView.as_view(), name="core_backup_restore_delete"),
    path("core_backup_restore/<int:pk>/print/", views.CoreBackupRestorePrintView.as_view(), name="core_backup_restore_print"),
    path("core_backup_restore/analytics/", views.CoreBackupRestoreAnalyticsView.as_view(), name="core_backup_restore_analytics"),
    path("core_backup_restore/export/csv/", views.export_core_backup_restore_csv, name="core_backup_restore_export_csv"),
    path("core_backup_restore/export/json/", views.export_core_backup_restore_json, name="core_backup_restore_export_json"),
]
