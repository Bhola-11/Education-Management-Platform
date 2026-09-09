"""Database Integrity Verification Command."""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = "Runs SQLite PRAGMA integrity_check to verify database health."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if row and row[0] == "ok":
                self.stdout.write(self.style.SUCCESS("SQLite database integrity check: OK"))
            else:
                self.stdout.write(self.style.ERROR(f"Integrity check failed: {row}"))
