"""Database Seeding Management Command for EduTrack Demo Cohorts."""
from django.core.management.base import BaseCommand
from core.models_core_base_models import CoreBaseModelsMaster

class Command(BaseCommand):
    help = "Seeds initial demo data across institutional apps."

    def handle(self, *args, **options):
        self.stdout.write("Seeding enterprise demo cohort...")
        obj, created = CoreBaseModelsMaster.objects.get_or_create(
            code="SEED-COHORT-2026",
            defaults={"name": "Standard Academic Cohort 2026", "capacity_limit": 500}
        )
        self.stdout.write(self.style.SUCCESS("Enterprise seed data populated successfully."))
