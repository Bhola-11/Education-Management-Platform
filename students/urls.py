"""
URL Routes for Students: Student Master Record
"""

from django.urls import path
from students import views_students_master_record as views

app_name = "students"

urlpatterns = [
    path("students_master_record/", views.StudentsMasterRecordListView.as_view(), name="students_master_record_list"),
    path("students_master_record/<int:pk>/", views.StudentsMasterRecordDetailView.as_view(), name="students_master_record_detail"),
    path("students_master_record/create/", views.StudentsMasterRecordCreateView.as_view(), name="students_master_record_create"),
    path("students_master_record/<int:pk>/edit/", views.StudentsMasterRecordUpdateView.as_view(), name="students_master_record_update"),
    path("students_master_record/<int:pk>/delete/", views.StudentsMasterRecordDeleteView.as_view(), name="students_master_record_delete"),
    path("students_master_record/<int:pk>/print/", views.StudentsMasterRecordPrintView.as_view(), name="students_master_record_print"),
    path("students_master_record/analytics/", views.StudentsMasterRecordAnalyticsView.as_view(), name="students_master_record_analytics"),
    path("students_master_record/export/csv/", views.export_students_master_record_csv, name="students_master_record_export_csv"),
    path("students_master_record/export/json/", views.export_students_master_record_json, name="students_master_record_export_json"),
]
