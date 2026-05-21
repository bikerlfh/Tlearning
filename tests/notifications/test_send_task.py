from unittest.mock import patch

import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from notifications.enums import NotificationStatus
from notifications.models import NotificationLog, PushSubscription
from notifications.tasks import send_push_notification


@pytest.mark.django_db
class TestSendPushNotification:
    def _setup(self, user, with_sub=True):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="cumbersome",
            source_language="en",
            target_language="es",
            data={"meaning": "heavy", "part_of_speech": "adjective"},
            source=ArtifactSource.MANUAL,
        )
        if with_sub:
            return PushSubscription.objects.create(
                user=user,
                endpoint="https://push.example.com/abc",
                p256dh_key="pk",
                auth_key="ak",
                user_agent="Chrome",
            )
        return None

    @patch("notifications.tasks.webpush")
    def test_sends_to_each_subscription(self, mock_webpush, user):
        sub = self._setup(user)
        send_push_notification(user.id)
        mock_webpush.assert_called_once()
        sub.refresh_from_db()
        assert sub.last_success_at is not None
        assert (
            NotificationLog.objects.filter(user=user, status=NotificationStatus.SENT).count() == 1
        )

    @patch("notifications.tasks.webpush")
    def test_no_due_card_skips_send(self, mock_webpush, user):
        self._setup(user)
        from reviews.enums import ReviewStatus
        from reviews.models import ReviewState

        ReviewState.objects.filter(artifact__user=user).update(status=ReviewStatus.LEARNED)
        send_push_notification(user.id)
        mock_webpush.assert_not_called()
        assert NotificationLog.objects.filter(user=user).count() == 0

    @patch("notifications.tasks.webpush")
    def test_410_deletes_subscription(self, mock_webpush, user):
        from pywebpush import WebPushException

        sub = self._setup(user)

        class FakeResponse:
            status_code = 410

        mock_webpush.side_effect = WebPushException("gone", response=FakeResponse())
        send_push_notification(user.id)
        assert not PushSubscription.objects.filter(id=sub.id).exists()
        assert (
            NotificationLog.objects.filter(user=user, status=NotificationStatus.FAILED).count() == 1
        )

    @patch("notifications.tasks.webpush")
    def test_other_error_increments_failure_count(self, mock_webpush, user):
        from pywebpush import WebPushException

        sub = self._setup(user)

        class FakeResponse:
            status_code = 500

        mock_webpush.side_effect = WebPushException("server error", response=FakeResponse())
        send_push_notification(user.id)
        sub.refresh_from_db()
        assert sub.failure_count == 1
        assert PushSubscription.objects.filter(id=sub.id).exists()
