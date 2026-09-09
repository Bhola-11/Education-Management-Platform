# EduTrack Enterprise System Architecture

EduTrack is designed following strict Model-View-Template (MVT) principles powered by Python 3.11, Django 5.0, and SQLite.

## Domain Modules
The platform organizes institutional logic across 17 specialized applications:
1. core
2. accounts
3. academics
4. students
5. teachers
6. enrollment
7. timetables
8. attendance
9. assignments
10. exams
11. grading
12. fees
13. library
14. certificates
15. notifications
16. dashboards
17. analytics

## Storage Subsystem
- SQLite 3 with Write-Ahead Logging (WAL) mode enabled.
- PRAGMA synchronous = NORMAL for optimal I/O throughput.
- PRAGMA foreign_keys = ON enforced across all connections.
