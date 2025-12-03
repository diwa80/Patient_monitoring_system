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
- `requirements.txt` — Python dependencies.

## 3. Features & Flows

- Sensor data ingestion: POST `/api/data` accepts JSON from devices (esp8266) with bed id, readings and triggers alerts + behavior detection.
- Dashboards: Admin and Nurse dashboards (`/admin/dashboard`, `/nurse/dashboard`) show KPIs and bed states.
- Alerts: stored in DB and accessible via API `/api/alerts` and UI; critical fall/bed-exit alerts create a modal notification and optional browser notifications.
- User management: Admins (and users with the `users` permission) can create users, assign menu permissions, edit, and delete users.
- Bed assignments: admins can assign nurses to beds via `/assignments`.

## 4. Database Schema (summary)

- `users` (id, username, password_hash, role ('admin'|'nurse'), menu_permissions (JSON text), status, created_at)
- `beds` (id, bed_name, room_no)
- `nurse_assignments` (nurse_id, bed_id)
- `readings` (bed_id, timestamp, temperature, humidity, motion, distance_cm)
- `alerts` (bed_id, alert_type, message, status, created_at, resolved_at)
- `devices`, `settings` tables for device status and configuration

Note: `menu_permissions` stored as JSON text on `users` to control per-user menu access.

## 5. Important Endpoints (HTTP)

- Page routes (GET): `/`, `/login`, `/logout`, `/users`, `/devices`, `/settings`, `/beds/<id>`, `/alerts`.
- API (GET/POST):
  - `POST /api/data` — sensor data ingestion
  - `GET /api/users` — list users (admin/permission guarded)
  - `POST /users/create` — create user (admin)
  - `POST /users/<id>/update` — update user (admin)
  - `POST /users/<id>/delete` — delete user (admin)
  - `POST /users/<id>/toggle` — toggle user active/disabled
  - `GET /api/beds` — list beds
  - `POST /assignments` — assign/unassign nurse to bed (admin)
  - `GET /api/alerts` — list alerts
  - `POST /api/alerts/<id>/resolve` — resolve alert

## 6. How to run (development)

Prerequisites: Python 3.10+ (project uses werkzeug, flask). Install requirements.

1. Create a virtual environment and install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Initialize the database (the app will call `init_db()` on start but you can run `python -c "from database import init_db; init_db()"` to be explicit).

3. Run the server:

```powershell
python server.py
```

4. Open `http://localhost:5000` and log in as admin. If no admin exists, use `create_admin.py` or create via DB.

## 7. Recent modifications (this branch/workspace)

- Replaced inline create-user card with a `Create New User` button and Bootstrap modal; modal includes `Assign Beds` multi-select and `Menu Permissions` checkboxes.
- Added edit/delete user actions in the users table and an Edit modal (without bed assignment in the edit modal as requested).
- Backend: stored `menu_permissions` in `users.menu_permissions` (JSON), created `models.update_user`, `models.delete_user`, and server endpoints `/users/<id>/update` and `/users/<id>/delete`.
- Permissions: added `permission_required(menu_key)` decorator and now load `menu_permissions` into `session` at login; sidebar respects these permissions.
- UI/UX: improved responsive CSS (`static/css/style.css`) with theme variables, better cards, table styling, and mobile tweaks.
- Auto-dismiss flash alerts: `base.html` includes a script to auto-close flash messages after 5 seconds (with Bootstrap and fallback handling).

## 8. Known issues & recommendations

- Editing a user's own menu permissions requires re-login to refresh `session['menu_permissions']`. Consider adding a session-refresh endpoint.
- Some UI flows still use `alert()` (native) for feedback; consider replacing with Bootstrap toasts for consistent UX.
- `menu_permissions` are currently top-level keys (`'users'`, `'devices'`, `'settings'`); for finer control, adopt hierarchical permission keys like `users.create`, `users.edit`.
- DB migrations are rudimentary (simple ALTER TABLE check in `database.init_db`). For production, use a proper migration tool (Alembic or similar).

## 9. Next recommended enhancements

1. Replace prompt-based bed assignment with a modal or per-user edit of assigned beds.
2. Convert notifications to Bootstrap toasts with configurable auto-hide time.
3. Add automated tests (unit tests for `models.py`, integration tests for API endpoints).
4. Add logging and Sentry (or similar) for production error tracking.
5. Add a small admin UI to manage settings stored in `settings` table programmatically.

---

If you want, I can:
- generate a PDF version of this report (`PROJECT_REPORT.pdf`),
- commit the report and open a PR, or
- expand any of the sections above into a more detailed design or user guide.

Report file created at: `PROJECT_REPORT.md` in the repository root.
