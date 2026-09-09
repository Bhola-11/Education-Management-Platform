"""
URL Routes for Enrollment: Course Registration
"""

from django.urls import path
from enrollment import views_enrollment_course_reg as views

app_name = "enrollment"

urlpatterns = [
    path("enrollment_course_reg/", views.EnrollmentCourseRegListView.as_view(), name="enrollment_course_reg_list"),
    path("enrollment_course_reg/<int:pk>/", views.EnrollmentCourseRegDetailView.as_view(), name="enrollment_course_reg_detail"),
    path("enrollment_course_reg/create/", views.EnrollmentCourseRegCreateView.as_view(), name="enrollment_course_reg_create"),
    path("enrollment_course_reg/<int:pk>/edit/", views.EnrollmentCourseRegUpdateView.as_view(), name="enrollment_course_reg_update"),
    path("enrollment_course_reg/<int:pk>/delete/", views.EnrollmentCourseRegDeleteView.as_view(), name="enrollment_course_reg_delete"),
    path("enrollment_course_reg/<int:pk>/print/", views.EnrollmentCourseRegPrintView.as_view(), name="enrollment_course_reg_print"),
    path("enrollment_course_reg/analytics/", views.EnrollmentCourseRegAnalyticsView.as_view(), name="enrollment_course_reg_analytics"),
    path("enrollment_course_reg/export/csv/", views.export_enrollment_course_reg_csv, name="enrollment_course_reg_export_csv"),
    path("enrollment_course_reg/export/json/", views.export_enrollment_course_reg_json, name="enrollment_course_reg_export_json"),
]
