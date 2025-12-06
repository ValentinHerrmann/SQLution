#!/bin/bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

mkdir -p tutorial/user_databases

docker compose -f compose.yaml down
docker compose -f compose.yaml pull
SQLUTION_IMAGE="${SQLUTION_IMAGE:-sqlution:local}" docker compose -f compose.yaml up -d --no-build --remove-orphans

# Ensure upload env vars have sensible defaults for local launches
export FILE_UPLOAD_MAX_MEMORY_SIZE="${FILE_UPLOAD_MAX_MEMORY_SIZE:-104857600}"
export DATA_UPLOAD_MAX_MEMORY_SIZE="${DATA_UPLOAD_MAX_MEMORY_SIZE:-104857600}"
export NGINX_CLIENT_MAX_BODY_SIZE="${NGINX_CLIENT_MAX_BODY_SIZE:-100M}"

rm -f ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt