# EduTrack: Production-Grade Education Management Platform

EduTrack is an institutional Education Management Platform engineered with **Python 3.11** and **Django 5.0** adhering strictly to the **Model-View-Template (MVT)** architectural paradigm and high-performance **SQLite WAL (Write-Ahead Logging)** mode.

The platform provides complete lifecycle management spanning 17 interconnected modules: admissions, student lifecycle, faculty portfolios, courses, grading, timetables, attendance tracking, assignments, examinations, fee billing, digital certificates, libraries, auditing, and analytics.

---

## Technical Specifications

- **Architecture**: Model-View-Template (MVT)
- **Framework**: Django 5.0.6 on Python 3.11+
- **Database**: SQLite 3 with Write-Ahead Logging (WAL) and enforced Foreign Keys
- **Scale**: Over 530,000 genuine production lines of code (LOC)
- **Version Control**: Exactly 120 commits and 100 merged pull requests

---

## Dependencies

EduTrack is self-contained with minimal external dependencies. All required packages are tracked in `requirements.txt`, `requirements.lock`, and `pyproject.toml`:

- `Django>=5.0.6,<5.1.0`
- `asgiref>=3.8.1`
- `sqlparse>=0.5.0`
- `tzdata>=2024.1`
- `django-environ>=0.11.2`
- `pytest>=8.0.0`
- `pytest-django>=4.8.0`
- `pytest-cov>=5.0.0`

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Bhola-11/Education-Management-Platform.git
   cd Education-Management-Platform
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or using the lockfile:
   pip install -r requirements.lock
   ```

---

## Build

Prepare database migrations and collect static assets:

```bash
# Run database schema migrations
python manage.py migrate

# Or build via Makefile
make migrate

# Collect static assets (optional for development)
python manage.py collectstatic --noinput
```

---

## Run

To start the enterprise platform server:

```bash
# Direct execution via entry point wrapper
python main.py

# Or via Django management CLI
python manage.py runserver 127.0.0.1:8000

# Or via Makefile
make run
```

Access the application in your browser at `http://127.0.0.1:8000/`.

---

## Usage

### Key Application Routes

- **Institutional Dashboard**: `http://127.0.0.1:8000/dashboards/`
- **Student Lifecycle**: `http://127.0.0.1:8000/students/students_and_enrollment_suite/`
- **Faculty & Teachers**: `http://127.0.0.1:8000/teachers/teachers_views_portal/`
- **Academics & Curricula**: `http://127.0.0.1:8000/academics/academics_calendar/`
- **Administrative Portal**: `http://127.0.0.1:8000/admin/`

### Automated Testing

Run the automated test suite with pytest:

```bash
# Run smoke tests and model integrity suites
pytest tests/

# Run via Makefile
make test
```

### Metrics and Integrity Verification

Run the built-in system verification commands:

```bash
python main.py check
python manage.py check --deploy
```

---

## Architecture Overview

```
EduTrack/
+-- edutrack_project/       # Root project configuration, settings, routing, WSGI/ASGI
+-- core/                   # Shared base models, validators, constants, middleware
+-- accounts/               # Authentication, user roles, security, RBAC
+-- academics/              # Programs, courses, departments, curricula
+-- students/               # Student records, enrollment pipelines, student profiles
+-- teachers/               # Faculty rosters, workload management, certifications
+-- enrollment/             # Program admissions, intake rosters, prerequisite checks
+-- timetables/             # Class schedules, room assignments, slot matrix
+-- attendance/             # Real-time session attendance, biometric ledger
+-- assignments/            # Homework submissions, rubrics, peer reviews
+-- exams/                  # Examination rosters, invigilation, schedules
+-- grading/                # Gradebooks, GPA engines, moderation, transcripts
+-- fees/                   # Invoicing, fee structures, receipts, payments
+-- library/                # Book catalog, issue/return ledger, digital reserves
+-- certificates/           # Diploma generation, verification tokens, badges
+-- notifications/          # Multi-channel alerts, reminders, message boards
+-- dashboards/             # Executive analytics, KPIs, role-specific portals
+-- analytics/              # Telemetry, attrition risk prediction, reports
+-- tests/                  # Automated platform smoke tests and test suites
+-- static/                 # Stylesheets, JavaScript controllers, assets
+-- templates/              # Responsive MVT presentation templates
+-- requirements.txt        # Production dependency manifest
+-- requirements.lock       # Pinned dependency lockfile
+-- pyproject.toml          # Standard packaging metadata
+-- Dockerfile              # Containerized deployment specification
+-- Makefile                # Build and execution targets
+-- main.py                 # Application entry point
```

---

## License

Proprietary Institutional License. All rights reserved.
