# 🚀 Simplified IDE Setup - One-Click Launch

## 📋 Overview

The IDE configurations have been simplified to provide **one optimal workflow**: Run Django in a Docker container with the debugger attached and browser automatically opened. Your IDE runs on the host for the best development experience.

---

## ✨ What You Get

### One Configuration, Perfect Workflow

**"Django in Container (Debug & Browser)"**

When you launch this configuration:
1. ✅ Docker container starts automatically
2. ✅ Django server starts in container with debugger
3. ✅ Debugger attaches from your IDE (on host)
4. ✅ Browser opens automatically to http://localhost:8000
5. ✅ Hot reload works for Python, templates, and static files
6. ✅ Set breakpoints and debug seamlessly

---

## 🔵 VS Code Setup

### Quick Start

1. **Open project in VS Code**
   ```bash
   code /path/to/SQLution
   ```

2. **Press F5 (or click Debug icon)**
   - Select: **"Django in Container (Debug & Browser)"**
   - Container starts automatically
   - Browser opens
   - Debugger attaches
   - Start coding!

### What Happens

```
Press F5
    ↓
Task: Start Django Container
    ↓
Container starts with Django + debugger waiting
    ↓
VS Code attaches debugger (port 5678)
    ↓
Browser opens to http://localhost:8000
    ↓
✅ Ready to develop!
```

### Features

- ✅ **One-click start**: Just press F5
- ✅ **Auto-attach**: Debugger connects automatically
- ✅ **Browser opens**: No manual navigation needed
- ✅ **Hot reload**: All file types auto-reload
- ✅ **Breakpoints**: Set breakpoints anywhere
- ✅ **Variable inspection**: Full debugging capabilities

---

## 🟢 PyCharm Setup

### Quick Start

1. **Open project in PyCharm**
   - File → Open → Select SQLution directory

2. **Start container first** (one time per session)
   ```bash
   ./dev-start.sh
   ```

3. **Click Debug** (or Shift+F9)
   - Select: **"Django in Container (Debug & Browser)"**
   - Browser opens automatically
   - Debugger attaches
   - Start coding!

### Configuration Details

**Type:** Python Remote Debug
- **Host:** localhost
- **Port:** 5678
- **Path Mappings:** 
  - Local: `$PROJECT_DIR$/tutorial`
  - Remote: `/workspace/tutorial`
- **Browser:** Auto-opens http://localhost:8000

### What Happens

```
Start container (./dev-start.sh)
    ↓
Container waits for debugger on port 5678
    ↓
Click Debug in PyCharm
    ↓
Browser opens to http://localhost:8000
    ↓
PyCharm attaches debugger
    ↓
✅ Ready to develop!
```

### Features

- ✅ **Remote debugging**: Full PyCharm debugging in container
- ✅ **Browser opens**: Automatic navigation
- ✅ **Hot reload**: All file types auto-reload
- ✅ **Breakpoints**: Professional debugging tools
- ✅ **Code completion**: Full IDE intelligence

---

## 🎯 Why This Setup?

### Best of Both Worlds

| Aspect | Solution | Benefit |
|--------|----------|---------|
| **Django** | Runs in Docker | Consistent, isolated environment |
| **IDE** | Runs on host | Fast, full features, no lag |
| **Debugger** | Remote attach | Full debugging capabilities |
| **Files** | Synced via volumes | Hot reload works perfectly |
| **Browser** | Auto-opens | Instant access, no manual steps |

### Optimal Workflow

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│             │      │                  │      │             │
│  IDE (Host) │◄─────┤ Debugger (5678) ├─────►│  Container  │
│             │      │                  │      │             │
└─────────────┘      └──────────────────┘      └──────┬──────┘
                                                      │
                                                      ▼
                                              Django Server (8000)
                                                      │
                                                      ▼
                                              Browser (Auto-opens)
```

---

## 🔧 How It Works

### Container Configuration

**compose.dev.yaml:**
- Waits for debugger by default (`WAIT_FOR_DEBUGGER=1`)
- Exposes port 5678 for debugging
- Exposes port 8000 for web server
- Mounts project files for hot reload

**dev-entrypoint.sh:**
- Starts static file watcher
- Runs Django with debugpy
- Waits for debugger to attach
- Starts serving requests

### IDE Configuration

**VS Code (launch.json):**
- Runs "Start Django Container" task first
- Attaches to port 5678
- Maps local → container paths
- Opens browser when server ready

**PyCharm (run configuration):**
- Remote debug connection to port 5678
- Path mappings configured
- Opens browser on launch
- Full debugging support

---

## 📝 Usage Guide

### Starting Development

#### VS Code
```bash
1. Open VS Code
2. Press F5
3. Wait for "Debugger attached" message
4. Browser opens automatically
5. Start coding!
```

#### PyCharm
```bash
1. Start container: ./dev-start.sh
2. Open PyCharm
3. Click Debug (or Shift+F9)
4. Browser opens automatically
5. Start coding!
```

### Stopping Development

#### VS Code
```bash
1. Press Shift+F5 (Stop debugging)
2. Container keeps running in background
3. To stop container: ./dev-stop.sh
```

#### PyCharm
```bash
1. Click Stop (or Ctrl+F2)
2. Container keeps running in background
3. To stop container: ./dev-stop.sh
```

### Setting Breakpoints

#### Both IDEs
```bash
1. Click left gutter next to line number
2. Red dot appears
3. Run code → execution pauses at breakpoint
4. Inspect variables, step through code
5. Continue execution (F5/F9)
```

---

## 🔍 Debugging Features

### What You Can Do

| Feature | VS Code | PyCharm |
|---------|---------|---------|
| **Breakpoints** | ✅ Yes | ✅ Yes |
| **Conditional Breakpoints** | ✅ Yes | ✅ Yes |
| **Step Over** | F10 | F8 |
| **Step Into** | F11 | F7 |
| **Step Out** | Shift+F11 | Shift+F8 |
| **Continue** | F5 | F9 |
| **Variable Inspection** | ✅ Yes | ✅ Yes |
| **Watch Expressions** | ✅ Yes | ✅ Yes |
| **Call Stack** | ✅ Yes | ✅ Yes |
| **Django Template Debug** | ✅ Yes | ✅ Yes |

---

## 🔥 Hot Reload

All file types auto-reload:

| File Type | Behavior | Time |
|-----------|----------|------|
| **Python** | Django restarts | ~1-2s |
| **Templates** | Instant reload | Immediate |
| **CSS/JS** | Auto-collected | ~1-2s |
| **Images** | Auto-collected | ~1-2s |

**No manual steps needed!** Just save and refresh browser.

---

## 🎓 Best Practices

### Do's ✅

- ✅ Use F5 (VS Code) or Debug button (PyCharm) to start
- ✅ Set breakpoints before running
- ✅ Keep container running between debug sessions
- ✅ Use hot reload - just save files
- ✅ Check console for errors

### Don'ts ❌

- ❌ Don't manually start container for VS Code (F5 does it)
- ❌ Don't restart container for every change
- ❌ Don't run Django locally and in container simultaneously
- ❌ Don't forget to stop container when done

---

## 🔧 Troubleshooting

### "Cannot connect to debugger"

**Solution:**
```bash
# Stop and restart container
./dev-stop.sh
./dev-start.sh

# Wait for "Waiting for debugger" message
# Then press F5 in IDE
```

### "Port 8000 already in use"

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or stop container
./dev-stop.sh
```

### "Browser doesn't open"

**Solution:**
- VS Code: Check serverReadyAction in launch.json
- PyCharm: Manually open http://localhost:8000
- Verify Django is running: `./dev-logs.sh`

### "Breakpoints not working"

**Solution:**
1. Verify debugger is attached (check IDE status)
2. Check path mappings are correct
3. Ensure `justMyCode: false` in VS Code
4. Try setting breakpoint earlier in code flow

---

## 📖 Related Documentation

- [DEV_SETUP.md](DEV_SETUP.md) - Complete development setup
- [DEVELOPMENT_MODES.md](DEVELOPMENT_MODES.md) - All development modes
- [scripts/README.md](../scripts/README.md) - Helper scripts

---

## 🎉 Summary

### VS Code
- **One configuration**: "Django in Container (Debug & Browser)"
- **One action**: Press F5
- **Result**: Container starts, debugger attaches, browser opens

### PyCharm
- **One configuration**: "Django in Container (Debug & Browser)"
- **Two steps**: Start container, click Debug
- **Result**: Debugger attaches, browser opens

### Benefits
✅ **Simple**: One configuration per IDE
✅ **Fast**: Quick to start
✅ **Powerful**: Full debugging
✅ **Convenient**: Browser auto-opens
✅ **Reliable**: Consistent environment

---

**🎊 Start developing with one click!**

Press F5 (VS Code) or Debug (PyCharm) and you're ready to code! 🚀
