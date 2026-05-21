import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact


@pytest.mark.django_db
class TestPostArtifact:
    url = "/api/v1/artifacts"

    def _payload(self, user, lemma="cumbersome"):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        return {
            "deck_id": str(deck.id),
            "type": ArtifactType.WORD,
            "lemma": lemma,
            "source_language": "en",
            "target_language": "es",
            "data": {"meaning": "heavy", "part_of_speech": "adjective"},
        }

    def test_create_new_artifact(self, authed_client, user):
        response = authed_client.post(self.url, self._payload(user), format="json")
        assert response.status_code == 201
        assert Artifact.objects.filter(user=user, lemma="cumbersome").exists()
        assert Artifact.objects.get(lemma="cumbersome").source == ArtifactSource.REST_API

    def test_upsert_updates_existing(self, authed_client, user):
        first = authed_client.post(self.url, self._payload(user), format="json").json()
        payload = self._payload(user)
        payload["data"] = {
            "meaning": "burdensome",
            "part_of_speech": "adjective",
            "examples": ["ex"],
        }
        response = authed_client.post(self.url, payload, format="json")
        assert response.status_code == 200  # 200 on update vs 201 on create
        assert response.json()["id"] == first["id"]
        a = Artifact.objects.get(id=first["id"])
        assert a.data["meaning"] == "burdensome"
        assert a.data["examples"] == ["ex"]

    def test_unauth_returns_401(self, api_client, user):
        response = api_client.post(self.url, self._payload(user), format="json")
        assert response.status_code in (401, 403)

    def test_cannot_create_in_other_users_deck(self, authed_client, other_user):
        from decks.models import Deck

        other_deck = Deck.objects.filter(user=other_user, is_default=True).first()
        payload = {
            "deck_id": str(other_deck.id),
            "type": ArtifactType.WORD,
            "lemma": "x",
            "source_language": "en",
            "target_language": "es",
            "data": {"meaning": "x", "part_of_speech": "noun"},
        }
        response = authed_client.post(self.url, payload, format="json")
        assert response.status_code == 400
