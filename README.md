More information about SQLution can be found at: 
[valentin-herrmann.com/sqlution](https://valentin-herrmann.com/sqlution/). 

The latest(minor) release is hosted at: [sqlution.de](https://sqlution.de/).

#### Deployment (containerized)
SQLution now ships with a Docker/Compose stack that is used both locally and on production (sqlution.de).

1. Copy `.env.example` to `.env` and adjust at least `SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`.
2. (Optional) Adjust the Compose resources/volumes in `compose.yaml` to match your server.
3. Launch or redeploy using Docker Compose:
	```bash
	docker compose -f compose.yaml up -d --build
	```

The container entrypoint automatically applies migrations and collects static files before starting gunicorn. A helper script (`update_and_launch.sh`) plus the GitHub release workflow automate the same steps on the production server. Resource requirements remain modest (≈1 vCPU, 1 GB RAM, 10 GB disk). Admins can monitor resource usage from inside the UI.

> **Static files**
>
> The app serves its own static assets via WhiteNoise from inside the container. To avoid clashes with legacy host-side `/static/` aliases (for example if an external nginx still owns that URL), deployments now set `DJANGO_STATIC_URL=/app-static/`. If you already proxy `/static/` directly to the Django container you can override this variable ( Compose/`docker run` both expose it ).

#### Versioning
The version number is stored in the VERSION file. The versioning follows the semantic versioning scheme (**major.intermediate.minor**). The minor number is incremented for small changes like aesthetics, small bug fixes or performance improvements. After merging a PR the minor version will usually be increased to make improvements available as fast as possible. The intermediate number is incremented for bigger features or several smaller features/bugfixes. The major number is incremented for breaking changes, disrupting features or major changes to the UI/UX. If backwards compatibility is broken it is mentioned in the release notes.

The release notes of intermediate versions list all changes since the last intermediate version. Planned intermediate versions are tracked as github milestones.

#### Contributing
Feel free to contribute to the project by forking it and creating a pull request. For larger changes please open an issue first to discuss the proposed changes. If you don't want to contribute code, you can also help by reporting bugs or suggesting features via the issue tracker.

