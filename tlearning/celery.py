import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tlearning.settings.dev")

app = Celery("tlearning")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
