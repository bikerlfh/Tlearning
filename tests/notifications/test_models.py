import pytest
from django.utils import timezone

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from notifications.enums import NotificationStatus
from notifications.models import NotificationLog, NotificationPreference, PushSubscription


@pytest.mark.django_db
class TestPushSubscription:
    def test_create(self, user):
        sub = PushSubscription.objects.create(
            user=user,
            endpoint="https://push.example.com/abc",
            p256dh_key="pk",
            auth_key="ak",
            user_agent="Chrome on Mac",
        )
        assert sub.failure_count == 0
        assert sub.last_success_at is None

    def test_endpoint_unique(self, user):
        from django.db import IntegrityError, transaction

        PushSubscription.objects.create(
            user=user,
            endpoint="https://x",
            p256dh_key="pk",
            auth_key="ak",
            user_agent="ua",
        )
        with pytest.raises(IntegrityError), transaction.atomic():
            PushSubscription.objects.create(
                user=user,
                endpoint="https://x",
                p256dh_key="pk2",
                auth_key="ak2",
                user_agent="ua2",
            )


@pytest.mark.django_db
class TestNotificationPreference:
    def test_auto_created_on_user_signup(self, user):
        pref = NotificationPreference.objects.get(user=user)
        assert pref.enabled is False
        assert pref.frequency_per_day == 4
        assert pref.min_interval_minutes == 120
        assert pref.quiet_hours_start.strftime("%H:%M") == "22:00"
        assert pref.quiet_hours_end.strftime("%H:%M") == "08:00"
        assert pref.weekdays_only is False


@pytest.mark.django_db
class TestNotificationLog:
    def test_create(self, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        a = Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="x",
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )
        log = NotificationLog.objects.create(
            user=user,
            artifact=a,
            sent_at=timezone.now(),
            status=NotificationStatus.SENT,
        )
        assert log.id is not None
