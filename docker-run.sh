#!/bin/bash

cd /var/www/wardenclyffe/wardenclyffe/
python manage.py migrate --noinput --settings=wardenclyffe.settings_docker
python manage.py collectstatic --noinput --settings=wardenclyffe.settings_docker
python manage.py compress --settings=wardenclyffe.settings_docker
exec gunicorn --env \
  DJANGO_SETTINGS_MODULE=wardenclyffe.settings_docker \
  wardenclyffe.wsgi:application -b 0.0.0.0:8000 -w 3 \
  --access-logfile=- --error-logfile=-
