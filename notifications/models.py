import datetime as dt
import uuid

from django.conf import settings
from django.db import models

from .enums import NotificationStatus


class PushSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions"
    )
    endpoint = models.TextField(unique=True)
    p256dh_key = models.CharField(max_length=200)
    auth_key = models.CharField(max_length=200)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["user", "failure_count"])]

    def __str__(self) -> str:
        return f"PushSub({self.user.email}, {self.user_agent[:30]})"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
        primary_key=True,
    )
    enabled = models.BooleanField(default=False)
    frequency_per_day = models.PositiveSmallIntegerField(default=4)
    min_interval_minutes = models.PositiveSmallIntegerField(default=120)
    quiet_hours_start = models.TimeField(default=dt.time(22, 0))
    quiet_hours_end = models.TimeField(default=dt.time(8, 0))
    weekdays_only = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Prefs({self.user.email}, enabled={self.enabled})"


class NotificationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_logs"
    )
    artifact = models.ForeignKey(
        "artifacts.Artifact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    sent_at = models.DateTimeField()
    clicked_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=NotificationStatus.choices)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [models.Index(fields=["user", "-sent_at"])]

    def __str__(self) -> str:
        return f"Notif({self.user.email}, {self.status})"
