#!/bin/bash

cd /var/www/wardenclyffe/wardenclyffe/
exec python manage.py celery beat --settings=wardenclyffe.settings_docker
