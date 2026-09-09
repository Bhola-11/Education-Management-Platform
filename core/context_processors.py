"""EduTrack Global Template Context Processors."""

from django.utils import timezone

def institute_settings(request):
    return {
        'INSTITUTE_NAME': getattr(request, 'institute_name', 'EduTrack Institute of Higher Education'),
        'ACADEMIC_YEAR': getattr(request, 'academic_year', '2025-2026'),
        'CURRENT_YEAR': timezone.now().year,
        'SYSTEM_VERSION': '1.0.0 Enterprise',
    }

def global_navigation(request):
    return {
        'MODULE_NAV_ITEMS': [
            {'name': 'Dashboards', 'url': '/dashboards/', 'icon': 'fas fa-chart-line'},
            {'name': 'Academics', 'url': '/academics/', 'icon': 'fas fa-graduation-cap'},
            {'name': 'Students', 'url': '/students/', 'icon': 'fas fa-user-graduate'},
            {'name': 'Teachers', 'url': '/teachers/', 'icon': 'fas fa-chalkboard-teacher'},
            {'name': 'Enrollment', 'url': '/enrollment/', 'icon': 'fas fa-user-plus'},
            {'name': 'Timetables', 'url': '/timetables/', 'icon': 'fas fa-calendar-alt'},
            {'name': 'Attendance', 'url': '/attendance/', 'icon': 'fas fa-user-check'},
            {'name': 'Assignments', 'url': '/assignments/', 'icon': 'fas fa-tasks'},
            {'name': 'Exams', 'url': '/exams/', 'icon': 'fas fa-file-alt'},
            {'name': 'Grading', 'url': '/grading/', 'icon': 'fas fa-award'},
            {'name': 'Fees & Billing', 'url': '/fees/', 'icon': 'fas fa-file-invoice-dollar'},
            {'name': 'Library', 'url': '/library/', 'icon': 'fas fa-book'},
            {'name': 'Certificates', 'url': '/certificates/', 'icon': 'fas fa-certificate'},
            {'name': 'Notifications', 'url': '/notifications/', 'icon': 'fas fa-bell'},
            {'name': 'Analytics', 'url': '/analytics/', 'icon': 'fas fa-chart-pie'},
            {'name': 'System & Core', 'url': '/core/', 'icon': 'fas fa-cogs'},
        ]
    }
