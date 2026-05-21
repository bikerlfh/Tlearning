import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from decks.models import Deck


@pytest.mark.django_db
class TestCrossUserIsolation:
    def _seed_other(self, other_user):
        deck = Deck.objects.filter(user=other_user, is_default=True).first()
        a = Artifact.objects.create(
            user=other_user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="hidden",
            source_language="en",
            target_language="es",
            data={"meaning": "x", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )
        return deck, a

    def test_list_artifacts_hides_others(self, authed_client, other_user):
        self._seed_other(other_user)
        response = authed_client.get("/api/v1/artifacts")
        assert all(a["lemma"] != "hidden" for a in response.json()["results"])

    def test_get_artifact_other_returns_404(self, authed_client, other_user):
        _, a = self._seed_other(other_user)
        response = authed_client.get(f"/api/v1/artifacts/{a.id}")
        assert response.status_code == 404

    def test_patch_artifact_other_returns_404(self, authed_client, other_user):
        _, a = self._seed_other(other_user)
        response = authed_client.patch(f"/api/v1/artifacts/{a.id}", {"lemma": "x"}, format="json")
        assert response.status_code == 404

    def test_delete_artifact_other_returns_404(self, authed_client, other_user):
        _, a = self._seed_other(other_user)
        response = authed_client.delete(f"/api/v1/artifacts/{a.id}")
        assert response.status_code == 404

    def test_list_decks_hides_others(self, authed_client, other_user):
        Deck.objects.create(
            user=other_user, name="hidden-deck", source_language="es", target_language="en"
        )
        response = authed_client.get("/api/v1/decks")
        assert all(d["name"] != "hidden-deck" for d in response.json()["results"])

    def test_get_deck_other_returns_404(self, authed_client, other_user):
        d = Deck.objects.create(
            user=other_user, name="x", source_language="es", target_language="en"
        )
        response = authed_client.get(f"/api/v1/decks/{d.id}")
        assert response.status_code == 404
