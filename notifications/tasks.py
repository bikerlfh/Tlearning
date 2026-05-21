"""Celery tasks for delivering push notifications."""

import json
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pywebpush import WebPushException, webpush

from accounts.models import User
from reviews.views import _due_queue

from .enums import NotificationStatus
from .models import NotificationLog

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

    payload = {
        "title": artifact.lemma,
        "body": _short_meaning(artifact),
        "data": {"artifact_id": str(artifact.id), "deck_id": str(artifact.deck_id)},
        "url": f"/study/{artifact.id}",
    }

    for sub in user.push_subscriptions.filter(failure_count__lt=_MAX_FAILURES):
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
            NotificationLog.objects.create(
                user=user,
                artifact=artifact,
                sent_at=timezone.now(),
                status=NotificationStatus.SENT,
            )
        except WebPushException as e:
            log.warning("Web push failed: %s", e)
            response = getattr(e, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code in (404, 410):
                sub.delete()
            else:
                sub.failure_count += 1
                sub.save(update_fields=["failure_count"])
            NotificationLog.objects.create(
                user=user,
                artifact=artifact,
                sent_at=timezone.now(),
                status=NotificationStatus.FAILED,
            )
