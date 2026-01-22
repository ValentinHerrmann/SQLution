More information about SQLution can be found at: 
[valentin-herrmann.com/sqlution](https://valentin-herrmann.com/sqlution/). 

The latest(minor) release is hosted at: [sqlution.de](https://sqlution.de/).

#### Dev
The OpenAPI configuration can be viewed in [Swagger Editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/ValentinHerrmann/SQLution/HEAD/openapi.yaml).


#### Deployment (containerized)
The repository ships with a Docker/Compose stack (`compose.yaml`) that mirrors the production container. Use it for local testing or for self-hosting on a VM where you control Docker Compose.

1. Copy `.env.example` to `.env`; set at least `SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and (optionally) `DJANGO_STATIC_URL`.
2. Review `compose.yaml` and tweak volumes/ports if your server layout differs (e.g. custom `USER_DATABASES_PATH`).
3. Build and launch:
	```bash
	docker compose -f compose.yaml up -d --build
	```

During image build the Dockerfile runs `collectstatic`, so the runtime container already contains optimized assets. At startup `docker/entrypoint.sh` only applies Django migrations before exec-ing gunicorn. Resource requirements remain modest (≈1 vCPU, 1 GB RAM, 10 GB disk). For legacy deployments you can still trigger `launch.sh` (and the fetch helper `update_and_launch.sh`) on the server, but the recommended path is now the GitHub Actions workflow described below.

> **Static files**
>
> The app serves its own static assets via WhiteNoise from inside the container. To avoid clashes with legacy host-side `/static/` aliases (for example if an external nginx still owns that URL), deployments now set `DJANGO_STATIC_URL=/app-static/`. If you already proxy `/static/` directly to the Django container you can override this variable ( Compose/`docker run` both expose it ).

#### GitHub Actions deployment workflow
- Workflow name: `Deploy` (`.github/workflows/deploy-on-release.yml`).
- Triggers: published GitHub Releases or manual `workflow_dispatch` with optional `deploy_ref` (branch/tag) input.
- Jobs:
	- `build_image`: updates the `VERSION` file, builds/pushes `ghcr.io/<owner>/sqlution`, tags both the commit SHA and the branch/ref.
	- `stop`: SSHes into the production host, stops/removes the running container, and garbage-collects old `sqlution` images.
	- `launch`: pulls the freshly built image on the server and runs it with the required environment.
- Required GitHub **secrets**: `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_REGISTRY_USER`, `DEPLOY_REGISTRY_TOKEN`, `DJANGO_SECRET_KEY`.
- Required GitHub **variables**: `DEPLOY_HOST`, `DEPLOY_PORT` (optional, defaults to `22`), `DEPLOY_APP_DIR`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_STATIC_URL` (defaults to `/app-static/`).
- Runtime configuration: the container exposes port `8000`, mounts the persistent `sqlution-db` volume plus `${DEPLOY_APP_DIR}/user_databases`, and picks up `SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_STATIC_URL`, and `SQLUTION_DB_DIR` from the workflow.
- Restart policy: deployments run the container with Docker's `--restart unless-stopped` flag so Debian-based hosts automatically bring it back after a reboot.
- Manual deploys: run the workflow from the Actions tab, select *Run workflow*, and optionally provide `deploy_ref` to deploy a specific branch or tag.

##### Using the workflow from a fork
- Fork owners must replicate the same **secrets/variables** listed above inside their fork’s repository settings (Settings ▸ Secrets and variables ▸ Actions).
- Secrets go under *Repository secrets*; variables go under *Repository variables*. Keep the identifiers identical (`DEPLOY_USER`, `DEPLOY_HOST`, …) so the workflow continues to resolve them via `${{ secrets.X }}` / `${{ vars.X }}`.
- Provide the `DEPLOY_APP_DIR` pointing to the directory on your server where the repo should live (e.g. `/opt/sqlution`).
- Ensure the target server has Docker installed, SSH key-based auth enabled for `DEPLOY_USER`, and network access to GHCR.
- If you need multiple environments, duplicate the workflow file or extend it with additional jobs keyed to different `environment:` names and corresponding secrets/variables.

#### Manual deployment from GHCR
1. Authenticate against GHCR (Personal Access Token with `read:packages` scope):
	```bash
	echo "${GITHUB_TOKEN}" | docker login ghcr.io -u <github-username> --password-stdin
	```
2. Pull the desired image (replace `<tag>` with branch/tag/SHA):
	```bash
	docker pull ghcr.io/<owner>/sqlution:<tag>
	```
3. Run the container manually (mirrors the workflow defaults and restart policy):
	```bash
	docker run -d --restart unless-stopped --name sqlution-app \
	  -p 8000:8000 \
	  -e SECRET_KEY='...' \
	  -e DJANGO_ALLOWED_HOSTS='sqlution.de,www.sqlution.de' \
	  -e DJANGO_STATIC_URL='/app-static/' \
	  -e SQLUTION_DB_DIR='/data' \
	  -v sqlution-db:/data \
	  -v /opt/sqlution/user_databases:/app/tutorial/user_databases \
	  ghcr.io/<owner>/sqlution:<tag>
	```
4. To update, stop/remove the old container and repeat the pull/run steps with the new tag.

#### Local debugging tips
- **Python venv**: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (or run the `venv_simple` VS Code task).
- **Runserver**: `python tutorial/manage.py runserver 0.0.0.0:8000` serves the app with hot reload; ensure `DJANGO_ALLOWED_HOSTS='*'` while debugging.
- **Docker Compose**: `docker compose up --build` mirrors production (uses the same Dockerfile, runs migrations, collects static files, serves via gunicorn).
- **Static assets**: when testing WhiteNoise locally, set `DJANGO_STATIC_URL=/app-static/` so paths match production.
- **Database snapshots**: the default SQLite DB lives under `tutorial/db.sqlite3`; delete it between tests or point `SQLUTION_DB_DIR` to a temp folder to start fresh.
- **Logs**: gunicorn output appears in the container logs (`docker logs -f sqlution-app`); Django runserver logs to stdout in venv mode.

#### Versioning
The version number is stored in the VERSION file. The versioning follows the semantic versioning scheme (**major.intermediate.minor**). The minor number is incremented for small changes like aesthetics, small bug fixes or performance improvements. After merging a PR the minor version will usually be increased to make improvements available as fast as possible. The intermediate number is incremented for bigger features or several smaller features/bugfixes. The major number is incremented for breaking changes, disrupting features or major changes to the UI/UX. If backwards compatibility is broken it is mentioned in the release notes.

The release notes of intermediate versions list all changes since the last intermediate version. Planned intermediate versions are tracked as github milestones.

#### Contributing
Feel free to contribute to the project by forking it and creating a pull request. For larger changes please open an issue first to discuss the proposed changes. If you don't want to contribute code, you can also help by reporting bugs or suggesting features via the issue tracker.
