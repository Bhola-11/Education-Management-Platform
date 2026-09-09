"""
EduTrack Enterprise Root URL Configuration.
Routes requests across 17 domain applications and administration.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboards/dashboards_librarian/', permanent=False), name='index'),
    
    # 17 Enterprise Domain Modules
    path('core/', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('academics/', include('academics.urls', namespace='academics')),
    path('students/', include('students.urls', namespace='students')),
    path('teachers/', include('teachers.urls', namespace='teachers')),
    path('enrollment/', include('enrollment.urls', namespace='enrollment')),
    path('timetables/', include('timetables.urls', namespace='timetables')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('assignments/', include('assignments.urls', namespace='assignments')),
    path('exams/', include('exams.urls', namespace='exams')),
    path('grading/', include('grading.urls', namespace='grading')),
    path('fees/', include('fees.urls', namespace='fees')),
    path('library/', include('library.urls', namespace='library')),
    path('certificates/', include('certificates.urls', namespace='certificates')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('dashboards/', include('dashboards.urls', namespace='dashboards')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
