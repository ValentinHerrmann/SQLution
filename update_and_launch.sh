set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

git fetch origin --tags --prune

TARGET_TAG="${DEPLOY_TAG:-$(git describe --tags $(git rev-list --tags --max-count=1))}"
git checkout "$TARGET_TAG" --force
git reset --hard "$TARGET_TAG"

./launch.sh