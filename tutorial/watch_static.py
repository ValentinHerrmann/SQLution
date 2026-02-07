#!/usr/bin/env python
"""
Static file watcher for Django development.
Automatically runs collectstatic when static files change.
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class StaticFilesEventHandler(FileSystemEventHandler):
    """Handle file system events for static files."""

    def __init__(self, debounce_seconds=1):
        self.debounce_seconds = debounce_seconds
        self.last_triggered = 0
        super().__init__()

    def should_trigger(self):
        """Check if enough time has passed since last trigger."""
        current_time = time.time()
        if current_time - self.last_triggered > self.debounce_seconds:
            self.last_triggered = current_time
            return True
        return False

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Only trigger for static files (js, css, html, etc.)
        if event.src_path.endswith(('.js', '.css', '.html', '.svg', '.png', '.jpg', '.gif')):
            if self.should_trigger():
                print(f"📁 Static file changed: {event.src_path}")
                self.run_collectstatic()

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith(('.js', '.css', '.html', '.svg', '.png', '.jpg', '.gif')):
            if self.should_trigger():
                print(f"📁 New static file: {event.src_path}")
                self.run_collectstatic()

    def run_collectstatic(self):
        """Run Django collectstatic command."""
        try:
            print("🔄 Running collectstatic...")
            result = subprocess.run(
                [sys.executable, 'manage.py', 'collectstatic', '--noinput', '--clear'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                print("✅ Static files collected successfully!")
            else:
                print(f"❌ Error collecting static files: {result.stderr}")
        except Exception as e:
            print(f"❌ Exception running collectstatic: {e}")


def main():
    """Main function to start the file watcher."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Directories to watch
    static_dirs = [
        project_root / 'myapp' / 'staticfiles',
        project_root / 'static',
    ]

    # Filter existing directories
    watch_dirs = [str(d) for d in static_dirs if d.exists()]

    if not watch_dirs:
        print("❌ No static directories found to watch!")
        return

    print("👀 Starting static file watcher...")
    print("📂 Watching directories:")
    for watch_dir in watch_dirs:
        print(f"   - {watch_dir}")
    print("\n✨ Static files will be automatically collected on changes")
    print("🛑 Press Ctrl+C to stop\n")

    # Create event handler and observer
    event_handler = StaticFilesEventHandler(debounce_seconds=1)
    observer = Observer()

    # Schedule watching for each directory
    for watch_dir in watch_dirs:
        observer.schedule(event_handler, watch_dir, recursive=True)

    # Start the observer
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping static file watcher...")
        observer.stop()

    observer.join()
    print("✅ Static file watcher stopped")


if __name__ == '__main__':
    main()
