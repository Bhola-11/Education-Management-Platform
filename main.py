#!/usr/bin/env python
"""
EduTrack Enterprise Platform Entry Point
Allows direct execution of the application or delegating administrative commands.
"""
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edutrack_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    if len(sys.argv) <= 1:
        print("Starting EduTrack Enterprise Platform Server on http://127.0.0.1:8000 ...")
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'])
    else:
        execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
