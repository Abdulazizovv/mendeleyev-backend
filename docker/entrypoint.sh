#!/usr/bin/env bash
set -e

mkdir -p /usr/src/app/logs /usr/src/app/media /usr/src/app/staticfiles /usr/src/app/celerybeat || true

# If running as root, fix volume permissions then drop privileges.
if [ "$(id -u)" = "0" ]; then
  chown -R django:django /usr/src/app/logs /usr/src/app/media /usr/src/app/staticfiles /usr/src/app/celerybeat || true
  exec gosu django "$0" "$@"
fi

# If a command is provided (e.g., celery/beat), run it.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting ASGI server..."
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
exec gunicorn -k uvicorn.workers.UvicornWorker core.asgi:application \
	--bind 0.0.0.0:8000 \
	--access-logfile - \
	--error-logfile - \
	--log-level "$LOG_LEVEL_LOWER"
