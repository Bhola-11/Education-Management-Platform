# EduTrack Enterprise Production Deployment Checklist

1. [x] Set SECRET_KEY via environment variable.
2. [x] Ensure DEBUG=False in production configurations.
3. [x] Run python manage.py migrate to apply relational schemas.
4. [x] Run python manage.py collectstatic to stage assets.
5. [x] Ensure SQLite database file permissions (rw-rw----) for WSGI/ASGI daemon.
6. [x] Verify SQLite WAL journal files reside on local filesystem.
