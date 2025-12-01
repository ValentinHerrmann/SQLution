set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

git fetch origin --tags --prune

TARGET_TAG="${DEPLOY_TAG:-$(git describe --tags $(git rev-list --tags --max-count=1))}"
git checkout "$TARGET_TAG" --force
git reset --hard "$TARGET_TAG"

docker compose -f compose.yaml build --pull
docker compose -f compose.yaml up -d --remove-orphans

rm -f ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt