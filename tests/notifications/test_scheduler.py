import datetime as dt
from unittest.mock import patch

import pytest
from django.utils import timezone

from notifications.models import NotificationPreference
from notifications.tasks import schedule_notifications_tick


@pytest.mark.django_db
class TestScheduleTick:
    @patch("notifications.tasks.send_push_notification.delay")
    def test_skips_disabled_users(self, mock_delay, user):
        pref = NotificationPreference.objects.get(user=user)
        assert pref.enabled is False
        schedule_notifications_tick()
        mock_delay.assert_not_called()

    @patch("notifications.tasks.send_push_notification.delay")
    def test_dispatches_when_enabled_and_in_active_window(self, mock_delay, user):
        pref = NotificationPreference.objects.get(user=user)
        pref.enabled = True
        # Quiet 00:00-00:01 — virtually never quiet, so we should fire
        pref.quiet_hours_start = dt.time(0, 0)
        pref.quiet_hours_end = dt.time(0, 1)
        pref.save()
        schedule_notifications_tick()
        mock_delay.assert_called_once_with(user.id)

    @patch("notifications.tasks.send_push_notification.delay")
    def test_skips_during_quiet_hours(self, mock_delay, user):
        pref = NotificationPreference.objects.get(user=user)
        pref.enabled = True
        pref.quiet_hours_start = dt.time(0, 0)
        pref.quiet_hours_end = dt.time(23, 59)
        pref.save()
        schedule_notifications_tick()
        mock_delay.assert_not_called()

    @patch("notifications.tasks.send_push_notification.delay")
    def test_skips_if_recent_send_within_min_interval(self, mock_delay, user):
        from notifications.enums import NotificationStatus
        from notifications.models import NotificationLog

        pref = NotificationPreference.objects.get(user=user)
        pref.enabled = True
        pref.quiet_hours_start = dt.time(0, 0)
        pref.quiet_hours_end = dt.time(0, 1)
        pref.min_interval_minutes = 60
        pref.save()
        NotificationLog.objects.create(
            user=user,
            sent_at=timezone.now() - dt.timedelta(minutes=10),
            status=NotificationStatus.SENT,
        )
        schedule_notifications_tick()
        mock_delay.assert_not_called()

    @patch("notifications.tasks.send_push_notification.delay")
    def test_skips_if_daily_limit_reached(self, mock_delay, user):
        from notifications.enums import NotificationStatus
        from notifications.models import NotificationLog

        pref = NotificationPreference.objects.get(user=user)
        pref.enabled = True
        pref.quiet_hours_start = dt.time(0, 0)
        pref.quiet_hours_end = dt.time(0, 1)
        pref.frequency_per_day = 2
        pref.min_interval_minutes = 1
        pref.save()
        for _ in range(2):
            NotificationLog.objects.create(
                user=user,
                sent_at=timezone.now() - dt.timedelta(minutes=30),
                status=NotificationStatus.SENT,
            )
        schedule_notifications_tick()
        mock_delay.assert_not_called()
