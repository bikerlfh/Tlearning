import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import ReviewStatus


@pytest.mark.django_db
class TestArtifactStatus:
    def _make(self, user, lemma="x", status=ReviewStatus.PENDING):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        a = Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma=lemma,
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )
        if status != ReviewStatus.PENDING:
            rs = a.review_state
            rs.status = status
            rs.save()
        return a

    def test_get_artifact_includes_status(self, authed_client, user):
        a = self._make(user)
        response = authed_client.get(f"/api/v1/artifacts/{a.id}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_list_artifacts_includes_status(self, authed_client, user):
        self._make(user, "a", ReviewStatus.PENDING)
        self._make(user, "b", ReviewStatus.LEARNED)
        response = authed_client.get("/api/v1/artifacts")
        by_lemma = {a["lemma"]: a["status"] for a in response.json()["results"]}
        assert by_lemma["a"] == "pending"
        assert by_lemma["b"] == "learned"

    def test_filter_by_status_pending(self, authed_client, user):
        self._make(user, "a", ReviewStatus.PENDING)
        self._make(user, "b", ReviewStatus.LEARNED)
        response = authed_client.get("/api/v1/artifacts?status=pending")
        lemmas = [a["lemma"] for a in response.json()["results"]]
        assert lemmas == ["a"]

    def test_filter_by_status_learned(self, authed_client, user):
        self._make(user, "a", ReviewStatus.PENDING)
        self._make(user, "b", ReviewStatus.LEARNED)
        response = authed_client.get("/api/v1/artifacts?status=learned")
        lemmas = [a["lemma"] for a in response.json()["results"]]
        assert lemmas == ["b"]
