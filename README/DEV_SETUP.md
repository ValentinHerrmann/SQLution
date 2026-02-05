# 🚀 SQLution Development Environment Guide

Complete guide for local development with hot reload support using dev-containers.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Workflow](#development-workflow)
- [Hot Reload Capabilities](#hot-reload-capabilities)
- [Helper Scripts](#helper-scripts)
- [VS Code Dev Container](#vs-code-dev-container)
- [Debugging](#debugging)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- 🔥 **Hot Reload** - Automatic reload for Python, Django templates, and static files
- 🐛 **Debugging Support** - Integrated debugpy for VS Code debugging
- 📦 **Dev Container** - Full VS Code dev container integration
- 🔧 **Helper Scripts** - Quick commands for common development tasks
- 🗄️ **Persistent Data** - Database and user files persist across restarts
- 🎯 **Isolated Environment** - Consistent development environment for all developers
- 📊 **Enhanced Logging** - Detailed logging for development debugging
- ⚡ **Fast Iteration** - Changes reflect immediately without rebuilds

## 📦 Prerequisites

- Docker Desktop or Docker Engine + Docker Compose
- (Optional) VS Code with Dev Containers extension
- Git

## 🚀 Quick Start

### Option 1: Using Helper Scripts (Recommended)

```bash
# Start the development environment
./dev-start.sh

# The server will be available at http://localhost:8000
# Default admin credentials: admin/admin
```

### Option 2: Using Docker Compose Directly

```bash
# Build and start
docker compose -f compose.dev.yaml up --build

# Or in detached mode
docker compose -f compose.dev.yaml up -d
```

### Option 3: Using VS Code Dev Container

1. Open the project in VS Code
2. Press `F1` and select "Dev Containers: Reopen in Container"
3. Wait for the container to build and initialize
4. Start developing!

## 🔄 Development Workflow

### Starting Development

```bash
# Start the environment
./dev-start.sh

# View logs
./dev-logs.sh

# Open a shell in the container
./dev-shell.sh
```

### Making Changes

1. **Python Files** - Edit any `.py` file → Django auto-reloads
2. **Templates** - Edit any `.html` template → Changes visible on refresh
3. **Static Files** - Edit JS/CSS files:
   ```bash
   # Collect static files (if needed)
   ./dev-manage.sh collectstatic --noinput
   # Or restart the container for full reload
   ```

### Running Django Commands

```bash
# Run any Django management command
./dev-manage.sh <command>

# Examples:
./dev-manage.sh migrate
./dev-manage.sh makemigrations
./dev-manage.sh createsuperuser
./dev-manage.sh shell
./dev-manage.sh test myapp
```

### Stopping Development

```bash
# Stop the container (preserves data)
./dev-stop.sh

# Stop and remove volumes (fresh start)
docker compose -f compose.dev.yaml down -v
```

## 🔥 Hot Reload Capabilities

### What Gets Auto-Reloaded?

| File Type | Hot Reload | Notes |
|-----------|------------|-------|
| **Python files** | ✅ Yes | Django's runserver auto-detects changes |
| **Django templates** | ✅ Yes | Changes visible on page refresh |
| **Static files (development)** | ⚡ Partial | Files are served from STATICFILES_DIRS |
| **Static files (after collectstatic)** | ✅ Yes | Run `collectstatic` to update |
| **Settings.py** | ✅ Yes | Server restarts automatically |
| **Models.py** | ⚠️ Requires migration | Run `makemigrations` + `migrate` |

### Optimization for Static Files

The development environment is configured to:
- Serve static files directly from source directories
- Skip compression for faster loading
- Enable Whitenoise auto-refresh in development mode
- Watch for file system changes

## 🛠️ Helper Scripts

All scripts are located in the project root:

### `dev-start.sh`
Starts the development environment with all necessary setup.
```bash
./dev-start.sh
```

### `dev-stop.sh`
Stops the development environment cleanly.
```bash
./dev-stop.sh
```

### `dev-logs.sh`
Follows container logs in real-time.
```bash
./dev-logs.sh
```

### `dev-shell.sh`
Opens an interactive bash shell in the running container.
```bash
./dev-shell.sh
```

### `dev-manage.sh`
Executes Django management commands.
```bash
./dev-manage.sh <command> [args...]
```

## 💻 VS Code Dev Container

### Opening in Dev Container

1. Install the "Dev Containers" extension in VS Code
2. Open the project folder
3. Click the green icon in the bottom-left corner
4. Select "Reopen in Container"

### What's Included

The dev container comes pre-configured with:
- Python environment with all dependencies
- Django debugging configuration
- Useful VS Code extensions:
  - Python
  - Django
  - Docker
  - ESLint
  - Prettier
- Git integration
- GitHub CLI

### Dev Container Features

- **Automatic Setup** - Dependencies install on container creation
- **Port Forwarding** - Ports 8000 and 5678 automatically forwarded
- **Volume Mounting** - Your code is mounted for live editing
- **Extensions** - Pre-configured extensions for Django development

## 🐛 Debugging

### VS Code Debugging

1. Start the environment with debugger support:
   ```bash
   # Set in .env file
   WAIT_FOR_DEBUGGER=1
   
   # Then start
   ./dev-start.sh
   ```

2. In VS Code, press `F5` or use the Debug panel
3. Select "Python: Remote Attach"
4. Configure launch.json:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Remote Attach",
         "type": "python",
         "request": "attach",
         "connect": {
           "host": "localhost",
           "port": 5678
         },
         "pathMappings": [
           {
             "localRoot": "${workspaceFolder}/tutorial",
             "remoteRoot": "/workspace/tutorial"
           }
         ]
       }
     ]
   }
   ```

### Setting Breakpoints

- Set breakpoints in VS Code by clicking the left margin
- Use `import pdb; pdb.set_trace()` for inline debugging
- Use `import ipdb; ipdb.set_trace()` for enhanced debugging (if installed)

### Viewing SQL Queries

To see SQL queries in the console:
```bash
# Add to .env
SQL_DEBUG=DEBUG

# Restart container
./dev-stop.sh && ./dev-start.sh
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Development Environment Variables
SECRET_KEY=dev-secret-key-change-in-production
DEBUG_MODE=True
DEVELOPMENT_MODE=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
SQLUTION_DB_DIR=/data

# Upload limits (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE=104857600
DATA_UPLOAD_MAX_MEMORY_SIZE=104857600

# Debugger (set to 1 to wait for debugger attachment)
WAIT_FOR_DEBUGGER=0

# SQL Query logging (set to DEBUG to see SQL queries)
SQL_DEBUG=INFO
```

### Custom Settings

Development-specific settings are automatically enabled when `DEVELOPMENT_MODE=True`:
- Static file serving without compression
- Enhanced logging
- SQL query logging (if SQL_DEBUG=DEBUG)
- Django Debug Toolbar (if installed)
- Disabled security restrictions for easier development

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f compose.dev.yaml logs

# Rebuild from scratch
docker compose -f compose.dev.yaml down -v
docker compose -f compose.dev.yaml build --no-cache
docker compose -f compose.dev.yaml up
```

### Hot Reload Not Working

```bash
# Check if container is running
docker compose -f compose.dev.yaml ps

# Restart the container
docker compose -f compose.dev.yaml restart

# Check file permissions
ls -la /workspace/tutorial
```

### Static Files Not Loading

```bash
# Collect static files
./dev-manage.sh collectstatic --noinput --clear

# Check static files configuration
./dev-manage.sh findstatic --verbosity 2 <filename>
```

### Database Issues

```bash
# Reset database
./dev-stop.sh
docker compose -f compose.dev.yaml down -v
./dev-start.sh

# Or migrate manually
./dev-manage.sh migrate
```

### Permission Issues

```bash
# Fix permissions (run on host)
sudo chown -R $USER:$USER tutorial/user_databases
sudo chmod -R 755 tutorial/user_databases
```

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or change the port in compose.dev.yaml
```

## 📝 Development Tips

### Testing Changes

```bash
# Run tests
./dev-manage.sh test

# Run specific test
./dev-manage.sh test myapp.tests.test_api

# Run with coverage
./dev-shell.sh
cd /workspace/tutorial
python -m pytest --cov=myapp --cov-report=html
```

### Database Management

```bash
# Create migrations
./dev-manage.sh makemigrations

# Apply migrations
./dev-manage.sh migrate

# Access Django shell
./dev-manage.sh shell

# Access database shell
./dev-manage.sh dbshell
```

### Creating Sample Data

```bash
# Use Django shell
./dev-manage.sh shell

# Then in the shell:
from django.contrib.auth.models import User
User.objects.create_superuser('admin', 'admin@test.com', 'admin')
```

### Monitoring Resources

```bash
# View container stats
docker stats sqlution-dev

# View disk usage
docker system df
```

## 🎓 Learning Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Docker Documentation](https://docs.docker.com/)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Python Debugging in VS Code](https://code.visualstudio.com/docs/python/debugging)

## 🤝 Contributing

When contributing, please:
1. Use the dev container for consistent environment
2. Run tests before committing: `./dev-manage.sh test`
3. Check code style: `black tutorial/` and `flake8 tutorial/`
4. Update documentation if adding new features

## 📄 License

See LICENSE file in the project root.

---

**Happy Coding! 🚀**

For issues or questions, check the troubleshooting section or open an issue on GitHub.
