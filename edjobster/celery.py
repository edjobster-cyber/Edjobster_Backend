import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edjobster.settings")

# Create Celery app
app = Celery("edjobster")

# Configure Celery using settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Explicitly set timezone (optional, ensures no confusion)
app.conf.enable_utc = False
app.conf.timezone = 'Asia/Kolkata'

# Import beat schedule
from .celery_beat_schedule import CELERY_BEAT_SCHEDULE
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
