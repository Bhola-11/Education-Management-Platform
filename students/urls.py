"""
URL Routes for Students: Student Portal & Directory
"""

from django.urls import path
from students import views_students_views_portal as views

app_name = "students"

urlpatterns = [
    path("students_views_portal/", views.StudentsViewsPortalListView.as_view(), name="students_views_portal_list"),
    path("students_views_portal/<int:pk>/", views.StudentsViewsPortalDetailView.as_view(), name="students_views_portal_detail"),
    path("students_views_portal/create/", views.StudentsViewsPortalCreateView.as_view(), name="students_views_portal_create"),
    path("students_views_portal/<int:pk>/edit/", views.StudentsViewsPortalUpdateView.as_view(), name="students_views_portal_update"),
    path("students_views_portal/<int:pk>/delete/", views.StudentsViewsPortalDeleteView.as_view(), name="students_views_portal_delete"),
    path("students_views_portal/<int:pk>/print/", views.StudentsViewsPortalPrintView.as_view(), name="students_views_portal_print"),
    path("students_views_portal/analytics/", views.StudentsViewsPortalAnalyticsView.as_view(), name="students_views_portal_analytics"),
    path("students_views_portal/export/csv/", views.export_students_views_portal_csv, name="students_views_portal_export_csv"),
    path("students_views_portal/export/json/", views.export_students_views_portal_json, name="students_views_portal_export_json"),
]
