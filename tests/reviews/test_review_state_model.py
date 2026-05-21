import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import FsrsState, ReviewStatus
from reviews.models import ReviewState


@pytest.mark.django_db
class TestReviewState:
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

    def test_create_review_state_defaults(self, user):
        a = self._make_artifact(user)
        # ReviewState is auto-created by post_save signal on Artifact.
        rs = a.review_state
        assert rs.state == FsrsState.NEW
        assert rs.status == ReviewStatus.PENDING
        assert rs.stability is None
        assert rs.difficulty is None
        assert rs.due_at is not None
        assert rs.reps == 0
        assert rs.lapses == 0

    def test_str(self, user):
        a = self._make_artifact(user)
        rs = a.review_state
        assert "x" in str(rs)

    def test_one_to_one_with_artifact(self, user):
        from django.db import IntegrityError, transaction

        a = self._make_artifact(user)
        # Signal already created one ReviewState; creating another must fail.
        with pytest.raises(IntegrityError), transaction.atomic():
            ReviewState.objects.create(artifact=a)
