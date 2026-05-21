import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tlearning.settings.dev")

app = Celery("tlearning")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "schedule-notifications-tick": {
        "task": "notifications.tasks.schedule_notifications_tick",
        "schedule": crontab(minute="*"),
    },
}
