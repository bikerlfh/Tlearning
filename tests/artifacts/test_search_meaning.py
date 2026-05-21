import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact


@pytest.mark.django_db
class TestSearchMeaning:
    def _seed(self, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="cumbersome",
            source_language="en",
            target_language="es",
            data={"meaning": "large, heavy, difficult to carry", "part_of_speech": "adjective"},
            source=ArtifactSource.MANUAL,
        )
        Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="featherlight",
            source_language="en",
            target_language="es",
            data={"meaning": "extremely light in weight", "part_of_speech": "adjective"},
            source=ArtifactSource.MANUAL,
        )

    def test_q_matches_lemma(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?q=cumbersome")
        assert response.json()["count"] == 1

    def test_q_matches_meaning(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?q=heavy")
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["lemma"] == "cumbersome"

    def test_q_matches_either_lemma_or_meaning(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?q=light")
        # 'light' appears in 'featherlight' lemma AND in its meaning ("light in weight")
        assert response.json()["count"] == 1

    def test_q_case_insensitive(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?q=HEAVY")
        assert response.json()["count"] == 1
