# Docker User Management Guide

## Overview
User accounts are stored in the SQLite database (`db.sqlite3`), which lives under `/data` inside the container and is persisted via the `sqlution-db` Docker volume. This means accounts will persist between container restarts and rebuilds.

## Persistent Storage
The following data is persisted across container runs:
- **Database**: `/data/db.sqlite3` → Docker volume `sqlution-db`
- **User Databases**: `/app/user_databases` → Docker volume `sqlution-userdata`

## Creating Admin/Superuser Accounts

### Method 1: Using the Helper Script (Easiest)
```bash
# Auto-detects sqlution-dev (debug) or sqlution-app (production)
./create_admin.sh

# Explicit container name (optional)
./create_admin.sh sqlution-app
```

### Method 2: Using Docker Exec Directly
```bash
# For debug container
docker exec -it sqlution-dev python manage.py createsuperuser

# For production container
docker exec -it <container-name> python manage.py createsuperuser
```

### Method 3: Using Django Admin Interface
1. Create an initial superuser using Method 1 or 2
2. Access Django admin at: http://localhost:8000/admin
3. Log in with your superuser credentials
4. Click "Users" → "Add User" to create additional accounts

## In-App Account Management (Accountverwaltung)

Day-to-day account management happens in the app at `/user_management/` ("Accountverwaltung" in the navigation). It is available to the global admin (`admin`) and to **group admins** (usually teachers).

- **Group admins**: the global admin creates an account for the teacher (for example `mueller_admin`, which also gives them their own project) and clicks the teacher icon in the account table. This adds the account to the Django group `Gruppenadmin`, which you can also manage in `/admin/`.
- **Creating accounts**: enter a list of names, or a base name plus a count, and optionally a **course prefix** (e.g. `q11inf` creates `q11inf-gruppe1_admin`). A prefix belongs to whoever uses it first and is released when its last account is deleted. Taken names are rejected, and a free name is suggested.
- **Passwords** are generated per account, or set as one shared password for the whole batch. They are shown **once**, with CSV download and a print view. If a password is lost, reset it.
- **Bulk actions**: lock and unlock, schedule a lock (`Sperren am`) or an automatic deletion (`Automatisch löschen am`), reset passwords, download data (a zip with one folder per account plus `accounts.csv`), and delete.
- **Deleting** asks you to type `LÖSCHEN`. It removes the account, its data folder, its sessions, review copies and brute-force records. Login audit logs are kept. Deleting a group admin also deletes every account they manage.
- **Review**: copies an account's project into a separate review slot (`user_databases/~review/<id>/`) and switches the teacher's session to it. The student's original and the teacher's own project are never changed. Use "Zurück zu meinem Projekt" in the banner to leave.

### Nutzer & Freigaben (db-users)

Once a db-admin account (`<name>_admin`) exists, its owner works independently under "Nutzer & Freigaben" (`/db_users/`):

- **db-users**: the db-admin creates accounts `<name>_<nutzer>` (e.g. `gruppe1_kasse`). They use the db-admin's project but can only run the released queries under "Nutzerfunktionen". Passwords are shown once (CSV/print), like in the Accountverwaltung. db-users can be locked, unlocked, given new passwords and deleted. Deleting a db-user keeps the project. db-users inherit the teacher, course prefix and scheduled dates of their db-admin, so the teacher sees them (listed below their db-admin) and deleting the db-admin deletes them too.
- **Freigaben**: a matrix of queries × db-users ("Alle" also covers db-users created later). New queries are visible to nobody but the db-admin. The settings are stored in `_zugriff.json` in the project folder, using the short names (`kasse`), so they are part of the project zip:

  ```json
  {"Preise": "*", "Umsatz": ["kasse"]}
  ```

- **Old projects**: the old file-name convention (`kasse_Umsatz.sql` visible only to `<name>_kasse`, files without `_` visible to everyone) is gone. The first time a project without `_zugriff.json` is opened, it is converted once: `kasse_Umsatz.sql` becomes `Umsatz.sql` released to `kasse`, `<<kasse_Umsatz>>` references are rewritten, and every renamed or changed file is backed up as `<name>.sql_bak` first. If the new name is taken, the file keeps its old name. Uploading an old project zip (without `_zugriff.json`) converts it the same way.
- Not available for db-admins whose name contains a further `_` (e.g. `max_mueller_admin`, see issue #89), and not while reviewing someone else's project.

### Scheduled locks and deletions

Scheduled locks and deletions are applied automatically: at most once a minute while the app receives requests, before every login, and immediately for a logged-in user whose time has passed. To apply them on a fixed schedule as well (for example from cron), run:

```bash
docker exec <container-name> python manage.py apply_account_schedules
```

## Creating Regular Users Programmatically

If you need to create users via script, you can create a Django management command:

```python
# tutorial/myapp/management/commands/create_user.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a regular user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **options):
        User.objects.create_user(
            username=options['username'],
            email=options['email'],
            password=options['password']
        )
        self.stdout.write(self.style.SUCCESS(f'User {options["username"]} created'))
```

Then use it:
```bash
docker exec sqlution-dev python manage.py create_user myuser user@example.com mypassword
```

## Managing Volumes

### View volumes
```bash
docker volume ls | grep sqlution
```

### Backup database
```bash
docker cp sqlution-dev:/data/db.sqlite3 ./backup_db.sqlite3
```

### Restore database
```bash
docker cp ./backup_db.sqlite3 sqlution-dev:/data/db.sqlite3
docker exec sqlution-dev chown appuser:appuser /data/db.sqlite3
```

### Remove volumes (WARNING: This deletes all data!)
```bash
docker compose -f compose.debug.yaml down -v
# or
docker volume rm sqlution-db sqlution-userdata
```

## Best Practices

1. **Never hardcode credentials in Dockerfile or compose files**
2. **Create admin accounts after container is running**
3. **Use environment variables for sensitive configuration** (already done for SECRET_KEY)
4. **Regularly backup your database volume**
5. **For production, consider using PostgreSQL instead of SQLite**
