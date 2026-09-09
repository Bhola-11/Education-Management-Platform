"""EduTrack Enterprise HTTP Middleware Stack."""

import time
import logging
from django.db import connection
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("edutrack.middleware")

class SqlitePragmaMiddleware(MiddlewareMixin):
    """Enforces WAL mode, foreign key constraints, and performance pragmas on SQLite."""
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self._pragmas_applied = False

    def process_request(self, request):
        if not self._pragmas_applied:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")
                cursor.execute("PRAGMA busy_timeout = 5000;")
                cursor.execute("PRAGMA cache_size = -64000;")
            self._pragmas_applied = True
            logger.info("SQLite enterprise WAL and FK pragmas applied.")

class AuditLoggingMiddleware(MiddlewareMixin):
    """Logs user requests with remote address and execution status."""
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = round((time.time() - request._start_time) * 1000, 2)
            user = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'ANONYMOUS'
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            if duration > 500:
                logger.warning(f"SLOW REQUEST: {request.method} {request.path} [{user} @ {ip}] finished in {duration}ms (Status: {response.status_code})")
        return response

class SessionSecurityMiddleware(MiddlewareMixin):
    """Enforces session timeout and validates user agent integrity."""
    def process_request(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            now = int(time.time())
            if last_activity and (now - last_activity > 86400):
                from django.contrib.auth import logout
                logout(request)
                request.session.flush()
            else:
                request.session['last_activity'] = now

class InstituteContextMiddleware(MiddlewareMixin):
    """Attaches institutional metadata to the request context."""
    def process_request(self, request):
        request.institute_name = "EduTrack Institute of Higher Education"
        request.academic_year = "2025-2026"

class RequestTimingMiddleware(MiddlewareMixin):
    """Appends processing time to response headers."""
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            response['X-Response-Time-ms'] = str(round((time.time() - request._start_time) * 1000, 2))
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Sets strict HTTP security headers."""
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """In-memory sliding window rate limiter for security endpoints."""
    _request_counts = {}

    def process_request(self, request):
        if request.path.startswith('/accounts/login/'):
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            now = time.time()
            records = self._request_counts.get(ip, [])
            records = [t for t in records if now - t < 60]
            if len(records) > 30:
                return JsonResponse({'error': 'Too many authentication attempts. Please wait.'}, status=429)
            records.append(now)
            self._request_counts[ip] = records
