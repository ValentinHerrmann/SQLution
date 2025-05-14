pkill gunicorn
source ../../bin/activate
git pull
pip install -r requirements.txt
cd tutorial
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput

rm /home/vale/github/django-tutorial/tutorial/last_launched.txt
date '+%Y-%m-%d %H:%M:%S' > /home/vale/github/django-tutorial/tutorial/last_launched.txt

nohup gunicorn --bind 0.0.0.0:8000 tutorial.wsgi &
