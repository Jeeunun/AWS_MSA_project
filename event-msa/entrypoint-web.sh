#!/bin/bash
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8002 --workers 3 --timeout 120 event_service.wsgi:application