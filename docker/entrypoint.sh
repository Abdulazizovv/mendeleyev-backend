#!/usr/bin/env bash
set -e

mkdir -p /usr/src/app/logs || true

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting ASGI server..."
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
exec gunicorn -k uvicorn.workers.UvicornWorker core.asgi:application \
	--bind 0.0.0.0:8000 \
	--access-logfile - \
	--error-logfile - \
	--log-level "$LOG_LEVEL_LOWER"
