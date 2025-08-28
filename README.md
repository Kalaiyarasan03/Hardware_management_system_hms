# Issue Tracker Django Project

This is a simple Django project scaffold for a store hardware issue tracking system with role-based access.

### Roles
- Employee: raise issues
- Hardware Team: view assigned issues, update status
- Manager: view all issues and assign/update

### Quick start (local)
1. Create virtualenv (recommended) and activate it.
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py createsuperuser` (to create admin)
5. Run server: `python manage.py runserver`
6. Login at `/accounts/login/` or use Django admin.

Notes:
- Default database: SQLite (`db.sqlite3`)
- Media files stored in `/media`
- Update `SECRET_KEY` before production and set `DEBUG=False`.


## Hardware team features
- Hardware dashboard: /hardware/
- Claim an issue: /issue/<id>/claim/
- Resolve: /issue/<id>/resolve/
- Add comments on issue detail page.
