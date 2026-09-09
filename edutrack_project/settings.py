"""
Django settings for EduTrack Enterprise Education Management Platform.
Configured for Python 3.11 + Django 5.0 with SQLite WAL mode and strict MVT.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'EDUTRACK_SECRET_KEY',
    'django-insecure-edutrack-enterprise-education-platform-master-key-2026-production'
)

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Core Enterprise Modules
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'academics.apps.AcademicsConfig',
    'students.apps.StudentsConfig',
    'teachers.apps.TeachersConfig',
    'enrollment.apps.EnrollmentConfig',
    'timetables.apps.TimetablesConfig',
    'attendance.apps.AttendanceConfig',
    'assignments.apps.AssignmentsConfig',
    'exams.apps.ExamsConfig',
    'grading.apps.GradingConfig',
    'fees.apps.FeesConfig',
    'library.apps.LibraryConfig',
    'certificates.apps.CertificatesConfig',
    'notifications.apps.NotificationsConfig',
    'dashboards.apps.DashboardsConfig',
    'analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # EduTrack Enterprise Custom Middleware
    'core.middleware.SqlitePragmaMiddleware',
    'core.middleware.AuditLoggingMiddleware',
    'core.middleware.SessionSecurityMiddleware',
    'core.middleware.InstituteContextMiddleware',
    'core.middleware.RequestTimingMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'edutrack_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.institute_settings',
                'core.context_processors.global_navigation',
                'notifications.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'edutrack_project.wsgi.application'
ASGI_APPLICATION = 'edutrack_project.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboards/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'EduTrack Notifications <notifications@edutrack.internal>'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'edutrack': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
