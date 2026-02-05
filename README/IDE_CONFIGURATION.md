# 🚀 IDE Configuration Guide - VS Code & PyCharm

Complete guide for launching and debugging SQLution in VS Code and PyCharm.

---

## 📋 Table of Contents

- [VS Code Configuration](#vs-code-configuration)
- [PyCharm Configuration](#pycharm-configuration)
- [Common Tasks](#common-tasks)
- [Debugging](#debugging)
- [Troubleshooting](#troubleshooting)

---

## 🔵 VS Code Configuration

### Quick Start

1. **Open Project in VS Code**
   ```bash
   code /path/to/SQLution
   ```

2. **Install Recommended Extensions** (when prompted)
   - Python
   - Pylance
   - Django
   - Docker
   - ESLint
   - Prettier

3. **Select Python Interpreter**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Select Interpreter"
   - Choose `.venv/bin/python`

### 🎯 Launch Configurations

Press `F5` or click the Run icon in the sidebar, then select:

#### Development Configurations

| Configuration | Description | Use When |
|--------------|-------------|----------|
| **Dev Container: Remote Attach** | Attach to running dev container | Using Docker development |
| **Django: Development Server (Local)** | Run Django locally without Docker | Quick local testing |
| **Django Full** | Full setup with migrations + static files | First time or after model changes |
| **Django Basic** | Simple Django server | Quick development |
| **Django Simple** | Minimal setup | Fastest startup |

#### Testing Configurations

| Configuration | Description |
|--------------|-------------|
| **Django: Run Tests (All)** | Run all project tests |
| **Django: Run Tests (myapp)** | Run only myapp tests |
| **Python: Pytest Current File** | Run tests in current file |

#### Utility Configurations

| Configuration | Description |
|--------------|-------------|
| **Django: Shell** | Open Django shell |
| **Python: Current File** | Run current Python file |
| **Containers: Python - Django** | Run in Docker with debugging |

### 🛠️ Tasks (Ctrl+Shift+P → "Tasks: Run Task")

#### Development Tasks

```
Dev: Start Development Server       # Start Docker dev environment
Dev: Stop Development Server        # Stop Docker dev environment
Dev: View Logs                      # View container logs
Dev: Open Shell                     # Open shell in container
Dev: Run Migrations                 # Apply database migrations
Dev: Make Migrations                # Create new migrations
Dev: Run Tests                      # Run all tests
Dev: Create Superuser               # Create admin user
Dev: Django Shell                   # Open Django shell
Dev: Collect Static Files           # Collect static files
```

#### Legacy Tasks (for non-Docker development)

```
venv                               # Setup virtual environment
venv_simple                        # Simple venv setup
makemigrations                     # Create migrations
migrate                            # Apply migrations
collectstatic                      # Collect static files
PreLaunchRoutine                   # Full setup routine
PreLaunchRoutine_simple            # Simple setup routine
```

#### Docker Tasks

```
Docker: Build Development Image     # Build dev Docker image
Docker: Start Development           # Start Docker Compose
Docker: Stop Development            # Stop Docker Compose
Docker: View Logs                   # View Docker logs
Docker: Restart Development         # Restart containers
```

#### Frontend Build Tasks

```
build sql ide                      # Build SQL IDE frontend
build apollon                      # Build Apollon diagram editor
sync embedded frontends            # Build and copy all frontends
```

### ⚙️ Settings

The project includes pre-configured settings in `.vscode/settings.json`:

- **Python**: Pylance language server with type checking
- **Linting**: Flake8 with 120 character line length
- **Formatting**: Black formatter (auto-format on save)
- **Testing**: Pytest integration
- **Django**: Template support with Emmet
- **File Exclusions**: Auto-hide __pycache__, .pytest_cache, etc.

### 🎨 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Start Debugging |
| `Ctrl+F5` | Run Without Debugging |
| `Shift+F5` | Stop Debugging |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+Shift+B` | Run Build Task (starts dev server) |
| `Ctrl+Shift+T` | Run Test Task |
| `Ctrl+`` | Toggle Terminal |

---

## 🟢 PyCharm Configuration

### Quick Start

1. **Open Project in PyCharm**
   - File → Open → Select SQLution directory

2. **Configure Python Interpreter**
   - File → Settings → Project → Python Interpreter
   - Click ⚙️ → Add → Virtualenv Environment
   - Select Existing: `.venv/bin/python`

3. **Enable Django Support**
   - File → Settings → Languages & Frameworks → Django
   - ✅ Enable Django Support
   - Django project root: `tutorial`
   - Settings: `tutorial/settings.py`
   - Manage script: `tutorial/manage.py`

### 🎯 Run Configurations

Pre-configured run configurations in `.idea/runConfigurations/`:

#### Main Configurations

| Configuration | Description | Icon |
|--------------|-------------|------|
| **Django Development Server** | Run Django dev server | ▶️ |
| **Docker: Development Container** | Run Docker Compose | 🐳 |
| **Run All Tests** | Execute all tests with pytest | 🧪 |

#### Management Commands

| Configuration | Description |
|--------------|-------------|
| **Django Shell** | Open Django shell |
| **Run Migrations** | Apply database migrations |
| **Make Migrations** | Create new migrations |
| **Collect Static Files** | Collect static files |

### 📦 Using Run Configurations

1. **Select Configuration**: Click dropdown in toolbar (top-right)
2. **Run**: Click ▶️ (Run) or 🐛 (Debug)
3. **Stop**: Click ⏹️ (Stop)

### 🔍 Debugging in PyCharm

1. **Set Breakpoints**: Click left gutter next to line numbers
2. **Start Debugging**: Select configuration and click 🐛
3. **Debug Controls**:
   - `F8` - Step Over
   - `F7` - Step Into
   - `Shift+F8` - Step Out
   - `F9` - Resume
   - `Alt+F9` - Run to Cursor

### ⚙️ Recommended PyCharm Settings

#### Code Style
- Settings → Editor → Code Style → Python
  - Tab size: 4
  - Max line length: 120
  - ✅ Use space indents

#### Django Templates
- Settings → Languages & Frameworks → Template Languages
  - Template Language: Django
  - Template Directories: `tutorial/myapp/templates`

#### File Watchers (Optional)
- Settings → Tools → File Watchers
  - Add Black formatter watcher
  - Add Flake8 watcher

### 🎨 PyCharm Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift+F10` | Run |
| `Shift+F9` | Debug |
| `Ctrl+Shift+F10` | Run context configuration |
| `Ctrl+F2` | Stop |
| `F8` | Step Over |
| `F7` | Step Into |
| `Alt+Shift+F10` | Select configuration and run |

---

## 🔄 Common Tasks

### Starting Development

#### VS Code
```bash
# Option 1: Use task
Ctrl+Shift+P → "Tasks: Run Task" → "Dev: Start Development Server"

# Option 2: Use launch config
F5 → Select "Dev Container: Remote Attach"

# Option 3: Use terminal
./dev-start.sh
```

#### PyCharm
```bash
# Option 1: Run configuration
Select "Django Development Server" → Click ▶️

# Option 2: Run Docker
Select "Docker: Development Container" → Click ▶️

# Option 3: Terminal
Alt+F12 → ./dev-start.sh
```

### Running Tests

#### VS Code
```bash
# Option 1: Launch configuration
F5 → "Django: Run Tests (All)"

# Option 2: Task
Ctrl+Shift+P → "Tasks: Run Task" → "Dev: Run Tests"

# Option 3: Test Explorer
Click Testing icon in sidebar → Run All Tests
```

#### PyCharm
```bash
# Option 1: Run configuration
Select "Run All Tests" → Click ▶️

# Option 2: Right-click
Right-click on tutorial/myapp/tests → "Run 'pytest in tests'"

# Option 3: Keyboard
Ctrl+Shift+F10 (while in test file)
```

### Database Migrations

#### VS Code
```bash
# Make migrations
Ctrl+Shift+P → "Tasks: Run Task" → "Dev: Make Migrations"

# Run migrations
Ctrl+Shift+P → "Tasks: Run Task" → "Dev: Run Migrations"

# Or use terminal
./dev-manage.sh makemigrations
./dev-manage.sh migrate
```

#### PyCharm
```bash
# Make migrations
Select "Make Migrations" → Click ▶️

# Run migrations
Select "Run Migrations" → Click ▶️

# Or use terminal
Alt+F12 → ./dev-manage.sh makemigrations
```

### Opening Django Shell

#### VS Code
```bash
# Option 1: Launch
F5 → "Django: Shell"

# Option 2: Task
Ctrl+Shift+P → "Tasks: Run Task" → "Dev: Django Shell"

# Option 3: Terminal
./dev-manage.sh shell
```

#### PyCharm
```bash
# Option 1: Run configuration
Select "Django Shell" → Click ▶️

# Option 2: Terminal
Alt+F12 → ./dev-manage.sh shell
```

---

## 🐛 Debugging

### Setting Up Debugging

#### VS Code - Docker Container Debugging

1. **Start container with debugger**:
   ```bash
   # Add to .env
   WAIT_FOR_DEBUGGER=1
   
   # Start container
   ./dev-start.sh
   ```

2. **Attach debugger**:
   - Press `F5`
   - Select "Dev Container: Remote Attach"
   - Debugger connects to port 5678

3. **Set breakpoints** and debug!

#### VS Code - Local Debugging

1. **Select configuration**:
   - Press `F5`
   - Choose "Django: Development Server (Local)"

2. **Set breakpoints** in code

3. **Run** - Server starts with debugger attached

#### PyCharm Debugging

1. **Set breakpoints**: Click left gutter
2. **Select configuration**: "Django Development Server"
3. **Click 🐛 (Debug)**: Server starts with debugger
4. **Use debug panel** to control execution

### Debug Features

| Feature | VS Code | PyCharm |
|---------|---------|---------|
| **Breakpoints** | Click gutter | Click gutter |
| **Conditional Breakpoints** | Right-click breakpoint | Right-click breakpoint |
| **Watch Variables** | Debug sidebar | Variables pane |
| **Evaluate Expression** | Debug console | Evaluate window |
| **Call Stack** | Debug sidebar | Frames pane |
| **Step Over** | `F10` | `F8` |
| **Step Into** | `F11` | `F7` |
| **Step Out** | `Shift+F11` | `Shift+F8` |
| **Continue** | `F5` | `F9` |

---

## 🔧 Troubleshooting

### VS Code Issues

#### "Python interpreter not found"
```bash
# Solution 1: Select interpreter
Ctrl+Shift+P → "Python: Select Interpreter" → Choose .venv/bin/python

# Solution 2: Recreate venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### "Module not found" errors
```bash
# Check PYTHONPATH
echo $PYTHONPATH  # Should include /workspace/tutorial

# Or set in terminal settings (already configured)
```

#### Tasks not running
```bash
# Make scripts executable
chmod +x dev-*.sh

# Verify scripts exist
ls -la dev-*.sh
```

### PyCharm Issues

#### "Django is not importable"
```bash
# Solution: Enable Django support
File → Settings → Languages & Frameworks → Django
✅ Enable Django Support
```

#### "No module named 'django'"
```bash
# Solution: Configure interpreter
File → Settings → Project → Python Interpreter
Add → Virtualenv → Existing: .venv/bin/python

# Or install requirements
pip install -r requirements.txt
```

#### Run configurations not showing
```bash
# Solution: Check .idea/runConfigurations/ exists
ls -la .idea/runConfigurations/

# Or reimport: File → Invalidate Caches / Restart
```

### Common Issues (Both IDEs)

#### Port 8000 already in use
```bash
# Find what's using it
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
python manage.py runserver 8001
```

#### Database locked
```bash
# Stop all instances
./dev-stop.sh

# Remove lock
rm tutorial/db.sqlite3-lock  # If it exists

# Restart
./dev-start.sh
```

#### Static files not loading
```bash
# Collect static files
./dev-manage.sh collectstatic --noinput --clear

# Or run task:
# VS Code: Ctrl+Shift+P → "Dev: Collect Static Files"
# PyCharm: Select "Collect Static Files" → Run
```

---

## 📖 Additional Resources

### VS Code
- [Python in VS Code](https://code.visualstudio.com/docs/languages/python)
- [Django in VS Code](https://code.visualstudio.com/docs/python/tutorial-django)
- [Debugging](https://code.visualstudio.com/docs/editor/debugging)

### PyCharm
- [Django Support](https://www.jetbrains.com/help/pycharm/django-support7.html)
- [Run/Debug Configurations](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html)
- [Debugging](https://www.jetbrains.com/help/pycharm/debugging-code.html)

### Project Documentation
- [DEV_SETUP.md](DEV_SETUP.md) - Complete development setup
- [DEV_QUICKREF.md](DEV_QUICKREF.md) - Quick reference
- [README.md](../README.md) - Project overview

---

## 🎉 Summary

### VS Code - Best For
- ✅ Lightweight and fast
- ✅ Docker/container development
- ✅ Multiple language support
- ✅ Extensive extension ecosystem
- ✅ Git integration

### PyCharm - Best For
- ✅ Full-featured Django IDE
- ✅ Advanced refactoring
- ✅ Database tools
- ✅ Intelligent code completion
- ✅ Professional debugging

### Both Support
- ✅ Hot reload development
- ✅ Debugging with breakpoints
- ✅ Django management commands
- ✅ Testing integration
- ✅ Git integration

---

**Choose your preferred IDE and start developing!** Both are fully configured and ready to use. 🚀

For questions or issues, check the troubleshooting section or refer to the main development documentation.
