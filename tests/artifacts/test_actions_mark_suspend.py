import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import ReviewStatus
from reviews.models import ReviewState


@pytest.mark.django_db
class TestArtifactActions:
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

    def test_mark_learned_sets_status(self, authed_client, user):
        a = self._make(user)
        response = authed_client.post(f"/api/v1/artifacts/{a.id}/mark-learned")
        assert response.status_code == 200
        rs = ReviewState.objects.get(artifact=a)
        assert rs.status == ReviewStatus.LEARNED

    def test_suspend_sets_status(self, authed_client, user):
        a = self._make(user)
        response = authed_client.post(f"/api/v1/artifacts/{a.id}/suspend")
        assert response.status_code == 200
        rs = ReviewState.objects.get(artifact=a)
        assert rs.status == ReviewStatus.SUSPENDED

    def test_mark_learned_other_user_404(self, authed_client, other_user):
        a = self._make(other_user)
        response = authed_client.post(f"/api/v1/artifacts/{a.id}/mark-learned")
        assert response.status_code == 404

    def test_suspend_other_user_404(self, authed_client, other_user):
        a = self._make(other_user)
        response = authed_client.post(f"/api/v1/artifacts/{a.id}/suspend")
        assert response.status_code == 404

    def test_suspended_card_excluded_from_queue(self, authed_client, user):
        a = self._make(user)
        authed_client.post(f"/api/v1/artifacts/{a.id}/suspend")
        response = authed_client.get("/api/v1/reviews/queue")
        lemmas = [c["lemma"] for c in response.json()["results"]]
        assert "x" not in lemmas

    def test_learned_card_excluded_from_queue(self, authed_client, user):
        a = self._make(user)
        authed_client.post(f"/api/v1/artifacts/{a.id}/mark-learned")
        response = authed_client.get("/api/v1/reviews/queue")
        lemmas = [c["lemma"] for c in response.json()["results"]]
        assert "x" not in lemmas
