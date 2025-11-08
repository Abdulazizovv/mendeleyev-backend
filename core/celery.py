import os
from celery import Celery

# Set default Django settings module for 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys
#   should have a `CELERY_` prefix in Django settings if using config_from_object
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Also discover non-standard task modules in specific apps
try:
    # Import apps.common.tasks_otp and apps.common.tasks_alerts explicitly via autodiscover
    app.autodiscover_tasks(packages=["apps.common"], related_name="tasks_otp")
    app.autodiscover_tasks(packages=["apps.common"], related_name="tasks_alerts")
except Exception:
    # Safe to ignore if module not present; regular autodiscovery will still work for tasks.py
    pass


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
