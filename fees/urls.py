"""
URL Routes for Fees: Fee Portals & Audit Views
"""

from django.urls import path
from fees import views_fees_portal_views as views

app_name = "fees"

urlpatterns = [
    path("fees_portal_views/", views.FeesPortalViewsListView.as_view(), name="fees_portal_views_list"),
    path("fees_portal_views/<int:pk>/", views.FeesPortalViewsDetailView.as_view(), name="fees_portal_views_detail"),
    path("fees_portal_views/create/", views.FeesPortalViewsCreateView.as_view(), name="fees_portal_views_create"),
    path("fees_portal_views/<int:pk>/edit/", views.FeesPortalViewsUpdateView.as_view(), name="fees_portal_views_update"),
    path("fees_portal_views/<int:pk>/delete/", views.FeesPortalViewsDeleteView.as_view(), name="fees_portal_views_delete"),
    path("fees_portal_views/<int:pk>/print/", views.FeesPortalViewsPrintView.as_view(), name="fees_portal_views_print"),
    path("fees_portal_views/analytics/", views.FeesPortalViewsAnalyticsView.as_view(), name="fees_portal_views_analytics"),
    path("fees_portal_views/export/csv/", views.export_fees_portal_views_csv, name="fees_portal_views_export_csv"),
    path("fees_portal_views/export/json/", views.export_fees_portal_views_json, name="fees_portal_views_export_json"),
]
