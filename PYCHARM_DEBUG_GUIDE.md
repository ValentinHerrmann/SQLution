# 🐍 PyCharm Debugging Setup Guide

## 🎯 Quick Start (Two Simple Steps)

### Step 1: Prepare Container
```bash
./pycharm-debug.sh
```
This script will:
- ✅ Start the container if not running
- ✅ Verify Django is waiting for debugger
- ✅ Show you the next steps

### Step 2: Attach Debugger in PyCharm
1. Select **"Attach to Django Container"** from the run configurations dropdown
2. Click the **Debug** button (🐛) or press `Shift+F9`
3. Browser opens automatically to http://localhost:8000
4. Set breakpoints and start debugging!

---

## 📋 Detailed Setup

### First-Time Configuration (One-Time Setup)

#### 1. Configure Python Interpreter (Optional but Recommended)

This helps PyCharm understand your code better:

1. **File → Settings** (or **PyCharm → Preferences** on Mac)
2. **Project: SQLution → Python Interpreter**
3. Click **⚙️ → Add**
4. Select **Virtualenv Environment**
5. Choose **Existing environment**
6. Browse to: `<project>/.venv/bin/python`
7. Click **OK**

#### 2. Enable Django Support (Optional but Recommended)

This provides better code completion for Django:

1. **File → Settings** (or **PyCharm → Preferences** on Mac)
2. **Languages & Frameworks → Django**
3. ✅ **Enable Django Support**
4. Set **Django project root**: `<project>/tutorial`
5. Set **Settings**: `tutorial/settings.py`
6. Set **Manage script**: `<project>/tutorial/manage.py`
7. Click **OK**

---

## 🚀 Daily Workflow

### Option A: Using Helper Script (Recommended)

```bash
# Terminal or PyCharm Terminal
./pycharm-debug.sh

# Then in PyCharm:
# Select "Attach to Django Container" → Click Debug (Shift+F9)
```

### Option B: Manual Steps

```bash
# 1. Start container
./dev-start.sh

# 2. Wait for message: "Waiting for debugger to attach on port 5678..."

# 3. In PyCharm:
#    Select "Attach to Django Container" → Click Debug (Shift+F9)
```

### Option C: Using PyCharm Run Configuration

1. Select **"Start Django Container"** → Click Run (Shift+F10)
2. Wait for container to start
3. Select **"Attach to Django Container"** → Click Debug (Shift+F9)

---

## 🔧 Available Run Configurations

### 1. "Start Django Container"
**Type:** Shell Script
**Purpose:** Starts the Docker container with Django

**When to use:**
- Container is not running
- You want to restart fresh

**What it does:**
- Runs `./dev-start.sh`
- Shows container logs in terminal
- Opens browser to http://localhost:8000

### 2. "Attach to Django Container"
**Type:** Python Debug Server
**Purpose:** Attaches PyCharm debugger to running Django in container

**When to use:**
- Container is already running
- Django is waiting for debugger

**What it does:**
- Connects to debugpy on port 5678
- Maps local code to container paths
- Enables breakpoints and debugging
- Opens browser automatically

---

## 🐛 Debugging Features

### Setting Breakpoints

1. Click in the left gutter next to line number
2. Red circle appears
3. Run debugger → execution pauses at breakpoint

### Conditional Breakpoints

1. Right-click on breakpoint
2. Enter condition (e.g., `user.id == 1`)
3. Breakpoint only triggers when condition is true

### Debug Controls

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Step Over** | `F8` | Execute current line, skip into functions |
| **Step Into** | `F7` | Step into function calls |
| **Step Out** | `Shift+F8` | Finish current function |
| **Resume** | `F9` | Continue to next breakpoint |
| **Evaluate** | `Alt+F8` | Evaluate expression |
| **Stop** | `Ctrl+F2` | Stop debugger |

### Debug Windows

- **Variables**: Shows all variables in current scope
- **Watches**: Monitor specific expressions
- **Frames**: Call stack
- **Console**: Python console in debug context
- **Threads**: View all threads

---

## 🔍 Troubleshooting

### "Cannot connect to localhost:5678"

**Cause:** Container not running or not waiting for debugger

**Solution:**
```bash
# Check container status
docker ps | grep sqlution-dev

# If not running, start it
./pycharm-debug.sh

# Or manually
./dev-start.sh

# Verify it's waiting
docker logs sqlution-dev | grep "Waiting for debugger"

# Then attach in PyCharm
```

### "Port 5678 is already in use"

**Cause:** Another process using debug port

**Solution:**
```bash
# Find process
lsof -i :5678

# Kill it
kill -9 <PID>

# Restart container
./dev-stop.sh
./dev-start.sh
```

### "Path mappings not working"

**Cause:** Incorrect local/remote path mapping

**Solution:**
1. Go to Run → Edit Configurations
2. Select "Attach to Django Container"
3. Verify Path Mappings:
   - Local: `<project>/tutorial`
   - Remote: `/workspace/tutorial`
4. Click OK

### Breakpoints not hit

**Possible causes and solutions:**

1. **Code not executed yet**
   - Solution: Trigger the code path (visit URL, run command)

2. **Debugger not attached**
   - Solution: Check "Debugger" tab shows "Connected"

3. **Wrong file version**
   - Solution: Verify file in container matches local
   - Run: `./dev-manage.sh collectstatic` if static file

4. **Breakpoint in wrong place**
   - Solution: Move breakpoint earlier in execution flow

### Container starts but debugger won't attach

**Cause:** WAIT_FOR_DEBUGGER may be set to 0

**Solution:**
```bash
# Check environment
docker exec sqlution-dev env | grep WAIT_FOR_DEBUGGER

# Should be 1 (or unset, defaults to 1)
# If it's 0, fix it:
echo "WAIT_FOR_DEBUGGER=1" >> .env

# Restart
./dev-stop.sh
./dev-start.sh
```

### "Module not found" errors

**Cause:** Python interpreter not configured

**Solution:**
1. Configure Python interpreter (see First-Time Configuration above)
2. Or ignore these errors - debugging will still work

---

## 💡 Tips & Best Practices

### Do's ✅

- ✅ Use `./pycharm-debug.sh` for easiest setup
- ✅ Keep container running between debug sessions
- ✅ Set breakpoints before starting debugger
- ✅ Use conditional breakpoints for specific cases
- ✅ Check "Debugger" tab to verify connection status
- ✅ Use "Evaluate Expression" (Alt+F8) to test code

### Don'ts ❌

- ❌ Don't run Django locally and in container simultaneously
- ❌ Don't forget to start container before attaching
- ❌ Don't set WAIT_FOR_DEBUGGER=0 unless you want to run without debugging
- ❌ Don't restart container for every change (hot reload works!)

---

## 🎯 Common Workflows

### Debug a Specific View

```bash
1. ./pycharm-debug.sh
2. Open the view file (e.g., views.py)
3. Set breakpoint in the view function
4. Attach debugger in PyCharm (Shift+F9)
5. Visit the URL in browser
6. Debugger pauses at breakpoint
7. Inspect variables, step through code
```

### Debug Django Management Command

```bash
1. Start container: ./dev-start.sh
2. Attach debugger in PyCharm
3. In PyCharm terminal:
   ./dev-manage.sh <command>
4. Breakpoints in command code will be hit
```

### Debug Template Rendering

```bash
1. ./pycharm-debug.sh
2. Set breakpoint in view that renders template
3. Attach debugger (Shift+F9)
4. Visit page
5. Step through to see template context
```

### Debug API Endpoint

```bash
1. ./pycharm-debug.sh
2. Set breakpoint in API view
3. Attach debugger
4. Use curl or Postman to call API
5. Debugger pauses, inspect request/response
```

---

## 📊 Understanding the Architecture

```
┌─────────────────┐
│ PyCharm (Host)  │  ← Your IDE runs here
│                 │
│ [Debug Client]  │  ← Debugger UI
└────────┬────────┘
         │
         │ TCP Connection (port 5678)
         │
         ↓
┌─────────────────────────┐
│ Docker Container        │
│                         │
│ ┌─────────────────────┐ │
│ │ debugpy Server      │ │  ← Debug server
│ └──────────┬──────────┘ │
│            │             │
│            ↓             │
│ ┌─────────────────────┐ │
│ │ Django (port 8000)  │ │  ← Your application
│ └─────────────────────┘ │
└─────────────────────────┘
         │
         ↓
┌─────────────────┐
│ Browser         │  ← Opens automatically
└─────────────────┘
```

**Key Points:**
- PyCharm on host connects to debugpy in container
- Code files synced via Docker volumes
- Breakpoints work because of path mappings
- Hot reload works for all file types

---

## 🎓 Learning Resources

### PyCharm Debugging
- [PyCharm Debugging Guide](https://www.jetbrains.com/help/pycharm/debugging-code.html)
- [Remote Debugging](https://www.jetbrains.com/help/pycharm/remote-debugging-with-product.html)

### Django Development
- [Django Documentation](https://docs.djangoproject.com/)
- [Django Debugging](https://docs.djangoproject.com/en/stable/topics/logging/)

### Docker
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 📖 Related Documentation

- [IDE_SIMPLIFIED.md](../IDE_SIMPLIFIED.md) - VS Code and PyCharm overview
- [DEV_SETUP.md](../DEV_SETUP.md) - Complete development setup
- [DEVELOPMENT_MODES.md](../DEVELOPMENT_MODES.md) - All development modes

---

## 🎉 Summary

### Quick Start Commands

```bash
# One command to set everything up:
./pycharm-debug.sh

# Then in PyCharm:
# Select "Attach to Django Container" → Shift+F9
```

### That's It!

✅ Container starts
✅ Django waits for debugger  
✅ PyCharm attaches
✅ Browser opens
✅ Debugging works!

**Happy debugging! 🐛🔍**
