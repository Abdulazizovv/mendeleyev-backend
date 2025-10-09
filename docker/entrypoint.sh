#!/usr/bin/env bash
set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting ASGI server..."
exec gunicorn -k uvicorn.workers.UvicornWorker core.asgi:application --bind 0.0.0.0:8000
