"""
URL Routes for Teachers: Faculty Master Record
"""

from django.urls import path
from teachers import views_teachers_master_record as views

app_name = "teachers"

urlpatterns = [
    path("teachers_master_record/", views.TeachersMasterRecordListView.as_view(), name="teachers_master_record_list"),
    path("teachers_master_record/<int:pk>/", views.TeachersMasterRecordDetailView.as_view(), name="teachers_master_record_detail"),
    path("teachers_master_record/create/", views.TeachersMasterRecordCreateView.as_view(), name="teachers_master_record_create"),
    path("teachers_master_record/<int:pk>/edit/", views.TeachersMasterRecordUpdateView.as_view(), name="teachers_master_record_update"),
    path("teachers_master_record/<int:pk>/delete/", views.TeachersMasterRecordDeleteView.as_view(), name="teachers_master_record_delete"),
    path("teachers_master_record/<int:pk>/print/", views.TeachersMasterRecordPrintView.as_view(), name="teachers_master_record_print"),
    path("teachers_master_record/analytics/", views.TeachersMasterRecordAnalyticsView.as_view(), name="teachers_master_record_analytics"),
    path("teachers_master_record/export/csv/", views.export_teachers_master_record_csv, name="teachers_master_record_export_csv"),
    path("teachers_master_record/export/json/", views.export_teachers_master_record_json, name="teachers_master_record_export_json"),
]
