"""Database Snapshot Exporter Command."""
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Creates a point-in-time snapshot backup of the SQLite database."

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        backup_path = Path(str(db_path) + ".backup")
        shutil.copy2(db_path, backup_path)
        self.stdout.write(self.style.SUCCESS(f"Snapshot exported to {backup_path}"))
