"""
URL Routes for Teachers: Faculty Portal & Directory
"""

from django.urls import path
from teachers import views_teachers_views_portal as views

app_name = "teachers"

urlpatterns = [
    path("teachers_views_portal/", views.TeachersViewsPortalListView.as_view(), name="teachers_views_portal_list"),
    path("teachers_views_portal/<int:pk>/", views.TeachersViewsPortalDetailView.as_view(), name="teachers_views_portal_detail"),
    path("teachers_views_portal/create/", views.TeachersViewsPortalCreateView.as_view(), name="teachers_views_portal_create"),
    path("teachers_views_portal/<int:pk>/edit/", views.TeachersViewsPortalUpdateView.as_view(), name="teachers_views_portal_update"),
    path("teachers_views_portal/<int:pk>/delete/", views.TeachersViewsPortalDeleteView.as_view(), name="teachers_views_portal_delete"),
    path("teachers_views_portal/<int:pk>/print/", views.TeachersViewsPortalPrintView.as_view(), name="teachers_views_portal_print"),
    path("teachers_views_portal/analytics/", views.TeachersViewsPortalAnalyticsView.as_view(), name="teachers_views_portal_analytics"),
    path("teachers_views_portal/export/csv/", views.export_teachers_views_portal_csv, name="teachers_views_portal_export_csv"),
    path("teachers_views_portal/export/json/", views.export_teachers_views_portal_json, name="teachers_views_portal_export_json"),
]
