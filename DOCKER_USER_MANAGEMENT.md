# Docker User Management Guide

## Overview
User accounts are stored in the SQLite database (`db.sqlite3`), which is now persisted using Docker volumes. This means accounts will persist between container restarts and rebuilds.

## Persistent Storage
The following data is persisted across container runs:
- **Database**: `/app/tutorial/db.sqlite3` → Docker volume `sqlution-db`
- **User Databases**: `/app/user_databases` → Docker volume `sqlution-userdata`

## Creating Admin/Superuser Accounts

### Method 1: Using the Helper Script (Easiest)
```bash
# For debug container (default)
./create_admin.sh

# For production container
./create_admin.sh sqlution
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
docker cp sqlution-dev:/app/tutorial/db.sqlite3 ./backup_db.sqlite3
```

### Restore database
```bash
docker cp ./backup_db.sqlite3 sqlution-dev:/app/tutorial/db.sqlite3
docker exec sqlution-dev chown appuser:appuser /app/tutorial/db.sqlite3
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
