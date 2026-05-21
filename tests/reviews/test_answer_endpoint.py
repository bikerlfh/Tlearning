import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import ReviewRating
from reviews.models import ReviewLog, ReviewState


@pytest.mark.django_db
class TestAnswerEndpoint:
    def _make(self, user, lemma="x"):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        return Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma=lemma,
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )

    def test_answer_good_advances_state_and_logs(self, authed_client, user):
        a = self._make(user)
        url = f"/api/v1/reviews/{a.id}/answer"
        response = authed_client.post(url, {"rating": ReviewRating.GOOD}, format="json")
        assert response.status_code == 200
        rs = ReviewState.objects.get(artifact=a)
        assert rs.reps == 1
        assert rs.last_reviewed_at is not None
        assert ReviewLog.objects.filter(artifact=a).count() == 1

    def test_answer_returns_next_card(self, authed_client, user):
        first = self._make(user, "first")
        self._make(user, "second")
        url = f"/api/v1/reviews/{first.id}/answer"
        response = authed_client.post(url, {"rating": ReviewRating.GOOD}, format="json")
        # response should include the next due card
        assert "next_card" in response.json()
        # next should be "second" (still NEW); first now has stability
        # and is scheduled in the future
        assert response.json()["next_card"]["lemma"] == "second"

    def test_answer_returns_null_next_when_queue_empty(self, authed_client, user):
        only = self._make(user, "only")
        url = f"/api/v1/reviews/{only.id}/answer"
        response = authed_client.post(url, {"rating": ReviewRating.EASY}, format="json")
        # After EASY, only card is rescheduled in the future → no other due
        assert response.json()["next_card"] is None

    def test_answer_invalid_rating_returns_400(self, authed_client, user):
        a = self._make(user)
        url = f"/api/v1/reviews/{a.id}/answer"
        response = authed_client.post(url, {"rating": 99}, format="json")
        assert response.status_code == 400

    def test_answer_other_user_artifact_returns_404(self, authed_client, other_user):
        a = self._make(other_user)
        url = f"/api/v1/reviews/{a.id}/answer"
        response = authed_client.post(url, {"rating": ReviewRating.GOOD}, format="json")
        assert response.status_code == 404
