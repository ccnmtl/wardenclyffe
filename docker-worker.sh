#!/bin/bash

cd /var/www/wardenclyffe/wardenclyffe/
exec python manage.py celery worker --settings=wardenclyffe.settings_docker -Q default,short,celery
