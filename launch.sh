#!/bin/bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

mkdir -p tutorial/user_databases

docker compose -f compose.yaml down
docker compose -f compose.yaml pull
SQLUTION_IMAGE="${SQLUTION_IMAGE:-sqlution:local}" docker compose -f compose.yaml up -d --no-build --remove-orphans

rm -f ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt