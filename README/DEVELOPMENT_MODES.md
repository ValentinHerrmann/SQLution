# 🚀 Development Setup Options & Static File Hot Reload

## 📋 Three Ways to Develop

SQLution offers **three different development modes**, each with its own advantages:

---

## 1️⃣ **Dev Container (VS Code)** - Full Isolation

### When to Use
- Working in VS Code
- Want complete environment isolation
- Need consistent setup across team
- First time setup

### How to Start
```bash
# In VS Code:
1. Press F1
2. Type "Dev Containers: Reopen in Container"
3. Wait for container to build
4. Start coding!
```

### What Runs Where
- ✅ **Everything in Docker**: Python, Django, database, static files
- ✅ **Code on host**: Files synced via volume mount
- ✅ **Hot reload**: Python ✅, Templates ✅, Static files ✅ (auto-collected)

### Features
- Full VS Code integration
- Extensions installed automatically
- Debugger pre-configured
- Python interpreter configured
- Terminal inside container

---

## 2️⃣ **Docker Compose Development** - Containerized with Host Tools

### When to Use
- Prefer command line
- Want Docker isolation
- Using PyCharm or other IDE
- Need reproducible environment

### How to Start
```bash
# Start development environment
./dev-start.sh

# View logs
./dev-logs.sh

# Stop when done
./dev-stop.sh
```

### What Runs Where
- ✅ **Django in Docker**: Python, Django, database
- ✅ **Code on host**: Files synced via volume mount
- ✅ **IDE on host**: Use any IDE (VS Code, PyCharm, etc.)
- ✅ **Hot reload**: Python ✅, Templates ✅, Static files ✅ (auto-collected)

### Features
- Docker isolation
- Easy start/stop scripts
- Works with any IDE
- Remote debugging support
- Persistent database

---

## 3️⃣ **Local Development** - Direct on Host

### When to Use
- Don't want Docker overhead
- Quick iterations
- Simple changes
- Testing locally

### How to Start
```bash
# Start local development with hot reload
./dev-local.sh

# Or manually:
source .venv/bin/activate
cd tutorial
python manage.py runserver
```

### What Runs Where
- ✅ **Everything on host**: Python, Django, database
- ✅ **No Docker**: Direct execution
- ✅ **Hot reload**: Python ✅, Templates ✅, Static files ✅ (auto-collected)

### Requirements
- Python 3.12+ installed
- Virtual environment created
- Dependencies installed

---

## 🔥 Static File Hot Reload

All three modes now support **automatic static file hot reload**!

### How It Works

1. **File Watcher**: Monitors `staticfiles/` directories
2. **Auto-Collect**: Runs `collectstatic` on changes
3. **Instant Reload**: Browser sees changes immediately

### Watched Files
- ✅ JavaScript (`.js`)
- ✅ CSS (`.css`)
- ✅ HTML templates (`.html`)
- ✅ Images (`.png`, `.jpg`, `.gif`, `.svg`)

### What You See

```bash
👀 Starting static file watcher...
📂 Watching directories:
   - /workspace/tutorial/myapp/staticfiles
   - /workspace/tutorial/static

📁 Static file changed: myapp/staticfiles/css/style_darkmode.css
🔄 Running collectstatic...
✅ Static files collected successfully!
```

### Behavior

| Change Type | Action | Time |
|-------------|--------|------|
| Edit `.js` file | Auto-collected | ~1-2 seconds |
| Edit `.css` file | Auto-collected | ~1-2 seconds |
| Edit `.html` template | Instant reload | Immediate |
| Edit `.py` file | Django restarts | ~1-2 seconds |
| Create new file | Auto-collected | ~1-2 seconds |
| Delete file | Auto-collected | ~1-2 seconds |

### Debouncing
- **1 second delay** between collects
- Prevents excessive collectstatic runs
- Handles bulk changes gracefully

---

## 🎯 Comparison Matrix

| Feature | Dev Container | Docker Compose | Local |
|---------|---------------|----------------|-------|
| **Isolation** | ✅ Full | ✅ Full | ❌ None |
| **Setup Time** | 🐢 Slow (first time) | 🐢 Slow (first time) | ⚡ Fast |
| **Performance** | 🐇 Good | 🐇 Good | 🚀 Best |
| **Hot Reload** | ✅ All files | ✅ All files | ✅ All files |
| **Static Reload** | ✅ Auto | ✅ Auto | ✅ Auto |
| **VS Code Integration** | ✅ Perfect | ⚠️ Manual | ⚠️ Manual |
| **PyCharm Support** | ❌ Limited | ✅ Yes | ✅ Yes |
| **Debugging** | ✅ Integrated | ✅ Remote | ✅ Direct |
| **Database** | 🐳 Docker | 🐳 Docker | 💾 SQLite local |
| **Consistency** | ✅ Perfect | ✅ Perfect | ⚠️ Varies |

---

## 📝 Quick Commands

### Dev Container (VS Code)
```bash
# Start
F1 → "Dev Containers: Reopen in Container"

# Stop
F1 → "Dev Containers: Reopen Folder Locally"
```

### Docker Compose
```bash
# Start
./dev-start.sh

# View logs
./dev-logs.sh

# Run Django commands
./dev-manage.sh migrate
./dev-manage.sh test

# Stop
./dev-stop.sh
```

### Local Development
```bash
# Start with hot reload
./dev-local.sh

# Or manual
source .venv/bin/activate
cd tutorial
python watch_static.py &  # Start file watcher
python manage.py runserver
```

---

## 🔧 Troubleshooting

### Static Files Not Updating?

**Check if watcher is running:**
```bash
# Docker: Check logs
./dev-logs.sh | grep "static file"

# Local: See watcher output
# Should show: "👀 Starting static file watcher..."
```

**Force collect:**
```bash
# Docker
./dev-manage.sh collectstatic --noinput --clear

# Local
python manage.py collectstatic --noinput --clear
```

### Watcher Not Starting?

**Check dependencies:**
```bash
# Docker: Rebuild
docker compose -f compose.dev.yaml build

# Local: Install watchdog
pip install watchdog
```

### Changes Not Visible?

1. **Hard refresh browser**: `Ctrl+F5` or `Cmd+Shift+R`
2. **Clear browser cache**
3. **Check file path**: Must be in `staticfiles/` or `static/`
4. **Restart server**: Stop and start again

### "workspaceFolder" Warning?

This warning is **harmless** when running Docker Compose outside VS Code:
```bash
# Ignore this warning - it's normal:
WARN[0000] The "workspaceFolder" variable is not set.
```

It only appears in terminal, not in VS Code dev container.

---

## 🎓 Recommendations

### For Beginners
👉 **Use Dev Container** (Option 1)
- Complete setup
- No configuration needed
- Works out of the box

### For Teams
👉 **Use Docker Compose** (Option 2)
- Consistent across team
- Easy onboarding
- Works with any IDE

### For Quick Changes
👉 **Use Local** (Option 3)
- Fastest startup
- Direct execution
- No Docker overhead

---

## 🚀 What Changed

### New Features
✅ **Static file watcher** (`watch_static.py`)
✅ **Auto-collectstatic** on file changes
✅ **Local dev script** (`dev-local.sh`)
✅ **Hot reload for all file types**
✅ **Debouncing** to prevent excessive runs

### Updated Files
- `requirements.txt` - Added `watchdog`
- `docker/dev-entrypoint.sh` - Starts file watcher
- `dev-local.sh` - New local development script
- `watch_static.py` - New file watcher

---

## 📚 Next Steps

1. **Choose your mode**: Dev Container, Docker, or Local
2. **Start developing**: Use the quick commands above
3. **Edit static files**: They auto-collect now!
4. **Check documentation**:
   - [DEV_SETUP.md](DEV_SETUP.md) - Full guide
   - [IDE_CONFIGURATION.md](IDE_CONFIGURATION.md) - IDE setup

---

**🎉 Now you have true hot reload for everything!**

Edit any file and see changes instantly:
- ✅ Python → Django restarts
- ✅ Templates → Instant reload
- ✅ Static files → Auto-collected
- ✅ Models → Migrate and restart

Happy coding! 🚀
