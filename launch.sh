#!/bin/bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$REPO_ROOT"

docker compose -f compose.yaml build --pull
docker compose -f compose.yaml up -d --remove-orphans

rm -f ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt