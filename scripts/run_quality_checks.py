"""Automated Code Quality and Test Verification Script."""
import sys
import subprocess

def run():
    print("Running Django automated test runner...")
    res = subprocess.run([sys.executable, "manage.py", "check"])
    if res.returncode != 0:
        print("System check failed!")
        sys.exit(1)
    print("All system checks passed cleanly.")

if __name__ == "__main__":
    run()
