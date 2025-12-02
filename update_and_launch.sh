set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

echo "$DEPLOY_TAG"
echo "$DEPLOY_REF"

git fetch origin --tags --prune

TARGET_IS_BRANCH=false
if [ -n "${DEPLOY_TAG:-}" ]; then
	TARGET_REF="$DEPLOY_TAG"
elif [ -n "${DEPLOY_REF:-}" ]; then
	TARGET_BRANCH="${DEPLOY_REF#origin/}"
	git fetch origin "${TARGET_BRANCH}" --depth=1
	TARGET_REF="origin/${TARGET_BRANCH}"
	TARGET_IS_BRANCH=true
else
	if [ -t 0 ]; then
		read -rp "Enter tag to deploy (leave empty to choose a branch): " MANUAL_TAG || true
	else
		MANUAL_TAG=""
	fi

	if [ -n "$MANUAL_TAG" ]; then
		TARGET_REF="$MANUAL_TAG"
	else
		if [ -t 0 ]; then
			read -rp "Enter branch to deploy (leave empty for current branch): " MANUAL_BRANCH || true
		else
			MANUAL_BRANCH=""
		fi

		if [ -n "$MANUAL_BRANCH" ]; then
			TARGET_BRANCH="$MANUAL_BRANCH"
		else
			TARGET_BRANCH=$(git rev-parse --abbrev-ref HEAD)
		fi

		git fetch origin "${TARGET_BRANCH}" --depth=1
		TARGET_REF="origin/${TARGET_BRANCH}"
		TARGET_IS_BRANCH=true
	fi
fi

if [ "$TARGET_IS_BRANCH" = true ]; then
	if git rev-parse --verify "$TARGET_BRANCH" >/dev/null 2>&1; then
		git checkout "$TARGET_BRANCH"
	else
		git checkout -b "$TARGET_BRANCH"
	fi
	git pull --ff-only origin "$TARGET_BRANCH"
	git reset --hard "origin/$TARGET_BRANCH"
else
	git checkout "$TARGET_REF" --force
 	git reset --hard "$TARGET_REF"
fi

bash launch.sh