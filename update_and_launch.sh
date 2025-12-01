set -euo pipefail

pkill gunicorn || true
source ../../bin/activate
git fetch --tags

TARGET_TAG="${DEPLOY_TAG:-$(git describe --tags `git rev-list --tags --max-count=1`)}"
git checkout "$TARGET_TAG"

pip install -r requirements.txt
cd tutorial
python3 manage.py makemigrations --merge
python3 manage.py migrate
python3 manage.py collectstatic --noinput

rm ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt

nohup gunicorn --bind 0.0.0.0:8000 tutorial.wsgi &