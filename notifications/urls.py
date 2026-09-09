"""
URL Routes for Notifications: Notification Center
"""

from django.urls import path
from notifications import views_notifications_center as views

app_name = "notifications"

urlpatterns = [
    path("notifications_center/", views.NotificationsCenterListView.as_view(), name="notifications_center_list"),
    path("notifications_center/<int:pk>/", views.NotificationsCenterDetailView.as_view(), name="notifications_center_detail"),
    path("notifications_center/create/", views.NotificationsCenterCreateView.as_view(), name="notifications_center_create"),
    path("notifications_center/<int:pk>/edit/", views.NotificationsCenterUpdateView.as_view(), name="notifications_center_update"),
    path("notifications_center/<int:pk>/delete/", views.NotificationsCenterDeleteView.as_view(), name="notifications_center_delete"),
    path("notifications_center/<int:pk>/print/", views.NotificationsCenterPrintView.as_view(), name="notifications_center_print"),
    path("notifications_center/analytics/", views.NotificationsCenterAnalyticsView.as_view(), name="notifications_center_analytics"),
    path("notifications_center/export/csv/", views.export_notifications_center_csv, name="notifications_center_export_csv"),
    path("notifications_center/export/json/", views.export_notifications_center_json, name="notifications_center_export_json"),
]
