# Development Scripts

This directory contains development and utility scripts for the SQLution project.

## Structure

```
scripts/
├── dev/              # Development environment scripts
│   ├── dev-start.sh      # Start Docker development environment
│   ├── dev-stop.sh       # Stop Docker development environment
│   ├── dev-logs.sh       # View development container logs
│   ├── dev-shell.sh      # Open shell in development container
│   ├── dev-manage.sh     # Run Django management commands
│   └── dev-local.sh      # Start local development (no Docker)
├── prod/             # Production deployment scripts
│   ├── launch.sh         # Launch production server
│   └── update_and_launch.sh  # Update and launch production
├── admin/            # Administration scripts
│   └── create_admin.sh   # Create admin user
└── README.md         # This file
```

## Development Scripts (`dev/`)

### Docker Development

**dev-start.sh** - Start the development environment
```bash
./scripts/dev/dev-start.sh
# Or use wrapper: ./dev-start.sh
```
- Builds and starts Docker Compose development environment
- Creates `.env` file if missing
- Shows logs automatically
- Container keeps running after Ctrl+C on logs

**dev-stop.sh** - Stop the development environment
```bash
./scripts/dev/dev-stop.sh
# Or use wrapper: ./dev-stop.sh
```
- Stops and removes development containers
- Preserves volumes (database, user files)

**dev-logs.sh** - View container logs
```bash
./scripts/dev/dev-logs.sh
# Or use wrapper: ./dev-logs.sh
```
- Follows logs from development container
- Press Ctrl+C to stop viewing (container keeps running)

**dev-shell.sh** - Open shell in container
```bash
./scripts/dev/dev-shell.sh
# Or use wrapper: ./dev-shell.sh
```
- Opens interactive bash shell in running container
- Useful for debugging and manual commands

**dev-manage.sh** - Run Django management commands
```bash
./scripts/dev/dev-manage.sh <command> [args...]
# Or use wrapper: ./dev-manage.sh <command> [args...]

# Examples:
./scripts/dev/dev-manage.sh migrate
./scripts/dev/dev-manage.sh makemigrations
./scripts/dev/dev-manage.sh createsuperuser
./scripts/dev/dev-manage.sh test
./scripts/dev/dev-manage.sh shell
```
- Executes any Django management command in the container

### Local Development

**dev-local.sh** - Start local development (no Docker)
```bash
./scripts/dev/dev-local.sh
# Or use wrapper: ./dev-local.sh
```
- Runs Django directly on host (no Docker)
- Activates virtual environment
- Runs migrations and collectstatic
- Starts file watcher for static files
- Starts Django development server
- Faster than Docker for quick iterations

---

## Production Scripts (`prod/`)

### Deployment & Launch

**launch.sh** - Launch production server
```bash
./scripts/prod/launch.sh
```
- Launches the production server
- Used for manual deployment

**update_and_launch.sh** - Update and launch production
```bash
./scripts/prod/update_and_launch.sh
```
- Updates the application
- Launches production server
- Used for production deployments

---

## Administration Scripts (`admin/`)

### User Management

**create_admin.sh** - Create admin user
```bash
./scripts/admin/create_admin.sh
```
- Creates Django admin superuser
- Interactive script for user creation

---

## Root Directory Wrappers

For convenience, wrapper scripts are provided in the root directory:
- `./dev-start.sh` → `./scripts/dev/dev-start.sh`
- `./dev-stop.sh` → `./scripts/dev/dev-stop.sh`
- `./dev-logs.sh` → `./scripts/dev/dev-logs.sh`
- `./dev-shell.sh` → `./scripts/dev/dev-shell.sh`
- `./dev-manage.sh` → `./scripts/dev/dev-manage.sh`
- `./dev-local.sh` → `./scripts/dev/dev-local.sh`

This allows you to use the scripts from anywhere without changing existing documentation or workflows.

## Usage

You can call scripts in three ways:

1. **From root directory using wrappers** (recommended):
   ```bash
   ./dev-start.sh
   ```

2. **Directly from scripts/dev**:
   ```bash
   ./scripts/dev/dev-start.sh
   ```

3. **From anywhere with full path**:
   ```bash
   /path/to/SQLution/scripts/dev/dev-start.sh
   ```

## Adding New Scripts

When adding new development scripts:

1. Place the script in `scripts/dev/`
2. Make it executable: `chmod +x scripts/dev/your-script.sh`
3. Create a wrapper in root if needed for convenience
4. Update this README
5. Update relevant documentation (DEV_SETUP.md, etc.)

## Related Documentation

- [DEV_SETUP.md](../README/DEV_SETUP.md) - Complete development environment guide
- [DEV_QUICKREF.md](../README/DEV_QUICKREF.md) - Quick reference for commands
- [DEVELOPMENT_MODES.md](../README/DEVELOPMENT_MODES.md) - Development mode options
- [IDE_CONFIGURATION.md](../README/IDE_CONFIGURATION.md) - IDE setup guide
