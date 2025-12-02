set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

git fetch origin --tags --prune

if [ -n "${DEPLOY_TAG:-}" ]; then
	TARGET_REF="$DEPLOY_TAG"
elif [ -n "${DEPLOY_REF:-}" ]; then
	git fetch origin "${DEPLOY_REF}" --depth=1 || git fetch origin "${DEPLOY_REF%/*}" --depth=1 || true
	TARGET_REF="$DEPLOY_REF"
else
	if [ -t 0 ]; then
		read -rp "Enter tag to deploy (leave empty to choose a branch): " MANUAL_TAG || true
	else
		MANUAL_TAG=""
	fi

	if [ -n "$MANUAL_TAG" ]; then
		TARGET_REF="$MANUAL_TAG"
	else
		CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
		TARGET_REF="origin/${CURRENT_BRANCH}"
	fi
fi

git checkout "$TARGET_REF" --force
git reset --hard "$TARGET_REF"

bash launch.sh