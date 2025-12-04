# Patient Monitoring System — Project Report

Last updated: 2025-12-03

This document summarizes the Patient Monitoring System repository: its purpose, structure, main components, runtime instructions, API surface, database schema essentials, and recent UI/feature changes.

---

## 1. Project Overview

- Purpose: a lightweight web application to monitor patient room environmental and activity data (temperature, humidity, motion, distance), detect abnormal behaviors (falls, bed exits, restlessness, fever), create alerts, and let staff (admins + nurses) view and manage beds and alerts.
- Stack: Python (Flask), SQLite, HTML/Jinja2 templates, Bootstrap 5, vanilla JavaScript, Chart.js.

## 2. Repo Layout (key files)

- `server.py` — Flask application, routes for pages and API endpoints, session and permission handling.
- `models.py` — data access layer, helper functions interacting with SQLite.
- `database.py` — DB initialization and migration helper.
- `schema.sql` — SQL schema used to create the DB.
- `create_admin.py` — (if present) helper to create an initial admin user.
- `templates/` — Jinja2 templates (pages and modals): `base.html`, `login.html`, `user_management.html`, `dashboard_admin.html`, `dashboard_nurse.html`, `bed_overview.html`, etc.
- `static/css/style.css` — custom styling and responsive rules.
- `static/js/main.js` — UI behaviors (sidebar, alerts, notifications, fall-alert monitoring).
## Archived: PROJECT_REPORT.md

The detailed project report was archived on 2025-12-04 and a copy is available at `archive/removed_files/PROJECT_REPORT.md`.

Original content removed from repo to declutter; archived copy retained.
- Dashboards: Admin and Nurse dashboards (`/admin/dashboard`, `/nurse/dashboard`) show KPIs and bed states.
