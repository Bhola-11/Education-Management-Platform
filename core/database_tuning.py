"""SQLite Database Engine Performance Tuning."""
from django.db import connection

def tune_sqlite_connection():
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA busy_timeout = 10000;")
        cursor.execute("PRAGMA cache_size = -128000;")
        cursor.execute("PRAGMA temp_store = MEMORY;")
