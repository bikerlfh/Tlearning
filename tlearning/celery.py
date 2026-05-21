import os
import ssl

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tlearning.settings.dev")

app = Celery("tlearning")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Upstash + most hosted Redis providers use `rediss://` (TLS). Celery refuses
# to connect without an SSL config in that case. Local dev / docker compose
# uses plain redis:// and falls through.
broker_url = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL", "")
if broker_url.startswith("rediss://"):
    ssl_opts = {"ssl_cert_reqs": ssl.CERT_NONE}
    app.conf.broker_use_ssl = ssl_opts
    app.conf.redis_backend_use_ssl = ssl_opts

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "schedule-notifications-tick": {
        "task": "notifications.tasks.schedule_notifications_tick",
        "schedule": crontab(minute="*"),
    },
}
