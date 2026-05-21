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

    def test_post_phrasal_verb_succeeds(self, authed_client, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        response = authed_client.post(
            "/api/v1/artifacts",
            {
                "deck_id": str(deck.id),
                "type": "phrasal_verb",
                "lemma": "come up with",
                "source_language": "en",
                "target_language": "es",
                "data": {
                    "meaning": "to think of (idea/solution)",
                    "particle": "up with",
                    "separable": False,
                    "register": "neutral",
                    "examples": ["She came up with a brilliant idea."],
                },
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        assert response.json()["type"] == "phrasal_verb"
        assert response.json()["data"]["particle"] == "up with"

    def test_post_phrasal_verb_missing_particle_returns_400(self, authed_client, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        response = authed_client.post(
            "/api/v1/artifacts",
            {
                "deck_id": str(deck.id),
                "type": "phrasal_verb",
                "lemma": "x",
                "source_language": "en",
                "target_language": "es",
                "data": {"meaning": "x"},
            },
            format="json",
        )
        assert response.status_code == 400
        assert "data" in response.json()

    def test_post_idiom_succeeds(self, authed_client, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        response = authed_client.post(
            "/api/v1/artifacts",
            {
                "deck_id": str(deck.id),
                "type": "idiom",
                "lemma": "to break the ice",
                "source_language": "en",
                "target_language": "es",
                "data": {
                    "meaning": "to start a conversation in a social setting",
                    "literal_translation": "romper el hielo",
                    "register": "neutral",
                    "examples": ["He told a joke to break the ice."],
                },
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        assert response.json()["data"]["literal_translation"] == "romper el hielo"

    def test_post_collocation_succeeds(self, authed_client, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        response = authed_client.post(
            "/api/v1/artifacts",
            {
                "deck_id": str(deck.id),
                "type": "collocation",
                "lemma": "make a decision",
                "source_language": "en",
                "target_language": "es",
                "data": {
                    "meaning": "to decide",
                    "pattern": "verb + noun",
                    "examples": ["Make a decision now."],
                },
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        assert response.json()["data"]["pattern"] == "verb + noun"

    def test_post_expression_succeeds(self, authed_client, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        response = authed_client.post(
            "/api/v1/artifacts",
            {
                "deck_id": str(deck.id),
                "type": "expression",
                "lemma": "cheers",
                "source_language": "en",
                "target_language": "es",
                "data": {
                    "meaning": "informal toast or casual thanks",
                    "context": "British informal",
                },
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        assert response.json()["data"]["context"] == "British informal"
