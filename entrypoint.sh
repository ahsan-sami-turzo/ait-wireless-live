#!/bin/bash

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
gunicorn Notifier.wsgi:application --env DJANGO_SETTINGS_MODULE=Notifier.settings --bind 0.0.0.0:8000