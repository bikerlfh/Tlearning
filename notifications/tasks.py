"""Celery tasks for delivering push notifications."""

import datetime as dt
import json
import logging
import zoneinfo

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pywebpush import WebPushException, webpush

from accounts.models import User
from reviews.views import _due_queue

from .enums import NotificationStatus
from .models import NotificationLog, NotificationPreference

log = logging.getLogger(__name__)

_MAX_FAILURES = 3


def _short_meaning(artifact, max_chars: int = 80) -> str:
    text = (artifact.data or {}).get("meaning", "")
    return text[: max_chars - 1] + "…" if len(text) > max_chars else text


def _pick_artifact_to_show(user):
    rs = _due_queue(user).first()
    return rs.artifact if rs else None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_push_notification(self, user_id):
    user = User.objects.get(pk=user_id)
    artifact = _pick_artifact_to_show(user)
    if artifact is None:
        return

    for sub in user.push_subscriptions.filter(failure_count__lt=_MAX_FAILURES):
        # Pre-create the log so its id can travel in the push payload and the
        # service worker can attribute click-throughs back to this row.
        notif_log = NotificationLog.objects.create(
            user=user,
            artifact=artifact,
            sent_at=timezone.now(),
            status=NotificationStatus.PENDING,
        )
        payload = {
            "title": artifact.lemma,
            "body": _short_meaning(artifact),
            "data": {
                "artifact_id": str(artifact.id),
                "deck_id": str(artifact.deck_id),
                "log_id": str(notif_log.id),
            },
            "url": f"/study/{artifact.id}",
        }
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh_key, "auth": sub.auth_key},
                },
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_CONTACT_EMAIL}"},
            )
            sub.last_success_at = timezone.now()
            sub.failure_count = 0
            sub.save(update_fields=["last_success_at", "failure_count"])
            notif_log.status = NotificationStatus.SENT
            notif_log.save(update_fields=["status"])
        except WebPushException as e:
            log.warning("Web push failed: %s", e)
            response = getattr(e, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code in (404, 410):
                sub.delete()
            else:
                sub.failure_count += 1
                sub.save(update_fields=["failure_count"])
            notif_log.status = NotificationStatus.FAILED
            notif_log.save(update_fields=["status"])


def _in_active_window(pref, local_now: dt.datetime) -> bool:
    if pref.weekdays_only and local_now.weekday() >= 5:
        return False
    start, end = pref.quiet_hours_start, pref.quiet_hours_end
    current = local_now.time()
    in_quiet = start <= current < end if start < end else current >= start or current < end
    return not in_quiet


def _sent_today_count(user, local_now: dt.datetime) -> int:
    since = timezone.now() - dt.timedelta(hours=24)
    return NotificationLog.objects.filter(
        user=user,
        status=NotificationStatus.SENT,
        sent_at__gte=since,
    ).count()


@shared_task
def schedule_notifications_tick():
    now = timezone.now()
    prefs = NotificationPreference.objects.filter(enabled=True).select_related("user")
    for pref in prefs:
        try:
            tz = zoneinfo.ZoneInfo(pref.user.timezone)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError):
            tz = zoneinfo.ZoneInfo("UTC")
        local_now = now.astimezone(tz)
        if not _in_active_window(pref, local_now):
            continue
        last = NotificationLog.objects.filter(user=pref.user).order_by("-sent_at").first()
        if last and (now - last.sent_at).total_seconds() < pref.min_interval_minutes * 60:
            continue
        if _sent_today_count(pref.user, local_now) >= pref.frequency_per_day:
            continue
        send_push_notification.delay(pref.user.id)
