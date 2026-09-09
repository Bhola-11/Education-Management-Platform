"""
URL Routes for Notifications: Notification Preferences
"""

from django.urls import path
from notifications import views_notifications_preferences as views

app_name = "notifications"

urlpatterns = [
    path("notifications_preferences/", views.NotificationsPreferencesListView.as_view(), name="notifications_preferences_list"),
    path("notifications_preferences/<int:pk>/", views.NotificationsPreferencesDetailView.as_view(), name="notifications_preferences_detail"),
    path("notifications_preferences/create/", views.NotificationsPreferencesCreateView.as_view(), name="notifications_preferences_create"),
    path("notifications_preferences/<int:pk>/edit/", views.NotificationsPreferencesUpdateView.as_view(), name="notifications_preferences_update"),
    path("notifications_preferences/<int:pk>/delete/", views.NotificationsPreferencesDeleteView.as_view(), name="notifications_preferences_delete"),
    path("notifications_preferences/<int:pk>/print/", views.NotificationsPreferencesPrintView.as_view(), name="notifications_preferences_print"),
    path("notifications_preferences/analytics/", views.NotificationsPreferencesAnalyticsView.as_view(), name="notifications_preferences_analytics"),
    path("notifications_preferences/export/csv/", views.export_notifications_preferences_csv, name="notifications_preferences_export_csv"),
    path("notifications_preferences/export/json/", views.export_notifications_preferences_json, name="notifications_preferences_export_json"),
]
