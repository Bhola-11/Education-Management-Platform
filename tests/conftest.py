import pytest
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edutrack_project.settings')

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
