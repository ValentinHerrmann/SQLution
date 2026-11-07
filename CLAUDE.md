# SQLution

## Working rules
- Start every response with "Vale".
- Stick to the existing coding style of the project.
- Don't add new code dependencies (pip packages, JS libraries, frameworks) without asking first. Vale must be able to understand the code quickly without learning anything new.
- Grill Vale when planning: ask about unclear requirements and edge cases before you build anything.
- PR are automatically checked by SonarQube; Make sure proactively that the quality gate passes and we have 0 issues.

## What the app is
A Django app for teaching databases/SQL in schools (sqlution.de). The UI text is German.
- Each project has its own folder `tutorial/user_databases/<base>/` with a SQLite DB, the saved queries (`<name>.sql`) and `_zugriff.json` (which db-user sees which query).
- Features: UML modelling with Apollon (`staticfiles/apollon`, converted to SQL by `utils/json_to_sql.py`), SQL IDE (Ace editor), "Nutzerfunktionen" (run saved queries; `{input}` and `{name}[dropdown SQL]` placeholders; a query named `Kategorie - Name` is grouped under the heading `Kategorie`), PDF export, zip/JSON import and export.

## Accounts (`_` is the separator, never part of a name)
- `admin`: the global admin (also uses the Django admin).
- Group admins (Django group `Gruppenadmin`, usually teachers) create and manage accounts and can review them (a copy goes into `user_databases/~review/<id>/`).
- `<base>_admin`: the db-admin, who owns the folder `<base>`.
- `<base>_<name>`: a db-user that works on the same folder and only sees released queries.
- A plain `<base>`: an old account.
- Folder and role helpers live in `utils/directories.py` (`get_user_directory`, `get_user_suffix`) and `utils/roles.py`.

## Code layout (`tutorial/myapp/`)
- `views/`: request handling only. `utils/`: business logic (`account_management`, `db_users`, `query_access`, `directories`, `roles`, `sqlite_connector`, `api_utils`).
- `templates/` (Bootstrap, base.html), `staticfiles/js|css` (plain JS, light/dark theme), `urls.py`, `models.py` (AccountProfile, AccountPrefix, AuditLog, ZippedFolder).
- `tests/`: pytest, run from `tutorial/`: `python manage.py migrate && python -m pytest -q`.
- Run locally: `python tutorial/manage.py runserver`. Deployment uses Docker and GitHub Actions (see README).
