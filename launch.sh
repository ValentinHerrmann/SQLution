source ../../bin/activate
cd tutorial

rm ./last_launched.txt
TZ=Europe/Berlin date '+%Y-%m-%d %H:%M:%S TZ=Eu/Ber' > ./last_launched.txt

nohup gunicorn --bind 0.0.0.0:8000 tutorial.wsgi &
