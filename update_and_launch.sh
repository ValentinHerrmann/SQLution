pkill gunicorn
source ../../bin/activate
git pull
pip install -r requirements.txt
cd tutorial/myapp/staticfiles/sql-ide
git checkout main
git pull
cd ../../..
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput

rm ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt

nohup gunicorn --bind 0.0.0.0:8000 tutorial.wsgi &
