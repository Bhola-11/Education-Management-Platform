"""
URL Routes for Notifications: Email Delivery Queue
"""

from django.urls import path
from notifications import views_notifications_email as views

app_name = "notifications"

urlpatterns = [
    path("notifications_email/", views.NotificationsEmailListView.as_view(), name="notifications_email_list"),
    path("notifications_email/<int:pk>/", views.NotificationsEmailDetailView.as_view(), name="notifications_email_detail"),
    path("notifications_email/create/", views.NotificationsEmailCreateView.as_view(), name="notifications_email_create"),
    path("notifications_email/<int:pk>/edit/", views.NotificationsEmailUpdateView.as_view(), name="notifications_email_update"),
    path("notifications_email/<int:pk>/delete/", views.NotificationsEmailDeleteView.as_view(), name="notifications_email_delete"),
    path("notifications_email/<int:pk>/print/", views.NotificationsEmailPrintView.as_view(), name="notifications_email_print"),
    path("notifications_email/analytics/", views.NotificationsEmailAnalyticsView.as_view(), name="notifications_email_analytics"),
    path("notifications_email/export/csv/", views.export_notifications_email_csv, name="notifications_email_export_csv"),
    path("notifications_email/export/json/", views.export_notifications_email_json, name="notifications_email_export_json"),
]
