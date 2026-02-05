# 🚀 IDE Quick Reference - VS Code & PyCharm

---

## VS Code

### 🎯 Quick Launch (F5)

| Configuration | Purpose |
|--------------|---------|
| `Dev Container: Remote Attach` | Debug Docker container |
| `Django: Development Server (Local)` | Run locally |
| `Django Full` | Full setup with migrations |
| `Django: Run Tests (All)` | Run all tests |

### ⌨️ Essential Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Start Debugging |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+Shift+B` | Build (Start Dev Server) |
| `Ctrl+Shift+T` | Run Tests |
| `Ctrl+`` | Toggle Terminal |

### 🛠️ Common Tasks

```bash
# Start dev server
Ctrl+Shift+P → "Dev: Start Development Server"

# Run migrations
Ctrl+Shift+P → "Dev: Run Migrations"

# Run tests
Ctrl+Shift+P → "Dev: Run Tests"

# Open shell
Ctrl+Shift+P → "Dev: Django Shell"
```

---

## PyCharm

### 🎯 Run Configurations

| Configuration | Purpose |
|--------------|---------|
| `Django Development Server` | Run Django |
| `Docker: Development Container` | Run Docker |
| `Run All Tests` | Run tests |
| `Django Shell` | Open shell |
| `Run Migrations` | Migrate DB |

### ⌨️ Essential Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift+F10` | Run |
| `Shift+F9` | Debug |
| `Ctrl+F2` | Stop |
| `F8` | Step Over |
| `F7` | Step Into |
| `Alt+F12` | Terminal |

### 🛠️ Common Actions

```bash
# Run configuration
Select config dropdown → Click ▶️

# Debug
Select config → Click 🐛

# Terminal command
Alt+F12 → ./dev-manage.sh <command>
```

---

## 🐛 Debugging

### VS Code - Docker Debug
```bash
1. Set WAIT_FOR_DEBUGGER=1 in .env
2. ./dev-start.sh
3. F5 → "Dev Container: Remote Attach"
```

### PyCharm - Local Debug
```bash
1. Set breakpoints (click gutter)
2. Select "Django Development Server"
3. Click 🐛 (Debug)
```

---

## 🔧 Quick Fixes

### "workspaceFolder variable not set" warning
```bash
# This warning is harmless when running outside VS Code
# Docker is working fine - you can safely ignore it
# The warning only appears in terminal, not in VS Code
```

### Port 8000 in use
```bash
lsof -i :8000
kill -9 <PID>
```

### Reset environment
```bash
./dev-stop.sh
docker compose -f compose.dev.yaml down -v
./dev-start.sh
```

### Static files issues
```bash
./dev-manage.sh collectstatic --noinput
```

---

## 📖 Full Documentation

See [IDE_CONFIGURATION.md](IDE_CONFIGURATION.md) for complete guide.
