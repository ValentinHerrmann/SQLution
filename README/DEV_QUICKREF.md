# 🚀 SQLution Development - Quick Reference

## 🏁 Getting Started

```bash
# Start development environment
./dev-start.sh

# Access the application
# → http://localhost:8000
# → admin/admin (default credentials)
```

**Note:** All dev scripts have wrappers in the root directory, but actual scripts are in `scripts/dev/`. Both work the same way!

## 🛠️ Common Commands

| Task | Command |
|------|---------|
| Start environment | `./dev-start.sh` |
| Stop environment | `./dev-stop.sh` |
| View logs | `./dev-logs.sh` |
| Open shell | `./dev-shell.sh` |
| Run Django command | `./dev-manage.sh <command>` |

## 📝 Django Commands

```bash
# Database
./dev-manage.sh migrate
./dev-manage.sh makemigrations
./dev-manage.sh dbshell

# Users
./dev-manage.sh createsuperuser
./dev-manage.sh changepassword <username>

# Testing
./dev-manage.sh test
./dev-manage.sh test myapp.tests.test_api

# Shell
./dev-manage.sh shell
./dev-manage.sh shell_plus  # if django-extensions installed

# Static files
./dev-manage.sh collectstatic
./dev-manage.sh findstatic <filename>

# Server (manual start if needed)
./dev-manage.sh runserver 0.0.0.0:8000
```

## 🔥 Hot Reload

| File Type | Auto-Reload | Action Needed |
|-----------|-------------|---------------|
| Python files | ✅ Automatic | None - just save |
| Templates | ✅ Automatic | Refresh browser |
| Static files | ✅ Automatic | Auto-collected via watcher |
| Models | ⚠️ Migration | `makemigrations` + `migrate` |

**New!** Static files are now automatically collected when changed. No manual `collectstatic` needed!

## 🐛 Debugging

```bash
# Enable debugger wait mode
# Add to .env:
WAIT_FOR_DEBUGGER=1

# Then restart
./dev-stop.sh && ./dev-start.sh

# In VS Code: Press F5 → "Dev Container: Remote Attach"
```

## 🔍 Troubleshooting

```bash
# Container won't start
docker compose -f compose.dev.yaml logs
docker compose -f compose.dev.yaml down -v
docker compose -f compose.dev.yaml up --build

# Hot reload not working
docker compose -f compose.dev.yaml restart

# Static files issues
./dev-manage.sh collectstatic --noinput --clear

# Database issues
./dev-stop.sh
docker compose -f compose.dev.yaml down -v
./dev-start.sh

# Permission issues (run on host)
sudo chown -R $USER:$USER tutorial/user_databases
```

## 📦 Inside Container

```bash
# Access container shell
./dev-shell.sh

# Then inside:
cd /workspace/tutorial
python manage.py <command>
pip install <package>
pytest
```

## 🌐 URLs

- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Debug Port**: 5678 (for remote debugging)

## 📂 Project Structure

```
SQLution/
├── tutorial/              # Django project
│   ├── manage.py
│   ├── tutorial/         # Settings & config
│   └── myapp/            # Main application
├── compose.dev.yaml      # Dev container config
├── Dockerfile.dev        # Dev image definition
├── dev-*.sh              # Helper scripts
└── .devcontainer/        # VS Code dev container
```

## 🔧 Environment Variables

Key variables in `.env`:

```bash
DEBUG_MODE=True               # Enable debug mode
DEVELOPMENT_MODE=True         # Enable dev features
SECRET_KEY=<your-key>        # Django secret
WAIT_FOR_DEBUGGER=0          # Wait for debugger (0/1)
SQL_DEBUG=INFO               # SQL logging (INFO/DEBUG)
```

## 💡 Tips

- **Fresh Start**: `docker compose -f compose.dev.yaml down -v && ./dev-start.sh`
- **View Logs**: Press Ctrl+C in `dev-start.sh` to exit logs (container keeps running)
- **Multiple Terminals**: Use `./dev-shell.sh` in another terminal
- **Performance**: Use `:cached` volume mounts (already configured)
- **Testing**: Run `pytest` with coverage inside container

## 📖 Full Documentation

See [DEV_SETUP.md](DEV_SETUP.md) for complete documentation.

---

**Need Help?** Check the troubleshooting section or run `./dev-logs.sh` to see what's happening.
