import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import FsrsState, ReviewStatus
from reviews.models import ReviewState


@pytest.mark.django_db
class TestReviewStateAutoCreate:
    def test_review_state_created_with_artifact(self, user):
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
        rs = ReviewState.objects.get(artifact=a)
        assert rs.state == FsrsState.NEW
        assert rs.status == ReviewStatus.PENDING

    def test_review_state_not_recreated_on_artifact_update(self, user):
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
        original_state_id = a.review_state.id
        a.lemma = "y"
        a.save()
        a.refresh_from_db()
        assert a.review_state.id == original_state_id
