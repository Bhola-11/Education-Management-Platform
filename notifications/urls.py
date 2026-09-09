"""
URL Routes for Notifications: Campus Broadcasts
"""

from django.urls import path
from notifications import views_notifications_broadcast as views

app_name = "notifications"

urlpatterns = [
    path("notifications_broadcast/", views.NotificationsBroadcastListView.as_view(), name="notifications_broadcast_list"),
    path("notifications_broadcast/<int:pk>/", views.NotificationsBroadcastDetailView.as_view(), name="notifications_broadcast_detail"),
    path("notifications_broadcast/create/", views.NotificationsBroadcastCreateView.as_view(), name="notifications_broadcast_create"),
    path("notifications_broadcast/<int:pk>/edit/", views.NotificationsBroadcastUpdateView.as_view(), name="notifications_broadcast_update"),
    path("notifications_broadcast/<int:pk>/delete/", views.NotificationsBroadcastDeleteView.as_view(), name="notifications_broadcast_delete"),
    path("notifications_broadcast/<int:pk>/print/", views.NotificationsBroadcastPrintView.as_view(), name="notifications_broadcast_print"),
    path("notifications_broadcast/analytics/", views.NotificationsBroadcastAnalyticsView.as_view(), name="notifications_broadcast_analytics"),
    path("notifications_broadcast/export/csv/", views.export_notifications_broadcast_csv, name="notifications_broadcast_export_csv"),
    path("notifications_broadcast/export/json/", views.export_notifications_broadcast_json, name="notifications_broadcast_export_json"),
]
