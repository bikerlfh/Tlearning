import time

import pytest
from django.utils import timezone

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import FsrsState, ReviewRating
from reviews.models import ReviewLog


@pytest.mark.django_db
class TestReviewLog:
    def _make_artifact(self, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        return Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="x",
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )

    def test_create_review_log(self, user):
        a = self._make_artifact(user)
        log = ReviewLog.objects.create(
            artifact=a,
            reviewed_at=timezone.now(),
            rating=ReviewRating.GOOD,
            elapsed_days=0.0,
            scheduled_days=2.0,
            state_before=FsrsState.NEW,
        )
        assert log.id is not None
        assert log.rating == ReviewRating.GOOD

    def test_ordering_recent_first(self, user):
        a = self._make_artifact(user)
        for r in [ReviewRating.AGAIN, ReviewRating.GOOD, ReviewRating.HARD]:
            ReviewLog.objects.create(
                artifact=a,
                reviewed_at=timezone.now(),
                rating=r,
                elapsed_days=0.0,
                scheduled_days=1.0,
                state_before=FsrsState.NEW,
            )
            time.sleep(0.01)  # ensure distinct reviewed_at
        ratings_in_order = [log.rating for log in ReviewLog.objects.filter(artifact=a)]
        assert (
            ratings_in_order[0] == ReviewRating.HARD
        )  # most recent first (ordering = ["-reviewed_at"])
