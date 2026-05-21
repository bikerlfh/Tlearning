import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact


@pytest.mark.django_db
class TestLanguageFilters:
    def _seed(self, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        seeds = [
            ("en", "es", "fast"),
            ("en", "es", "slow"),
            ("fr", "es", "vite"),
            ("pt", "es", "rapido"),
        ]
        for src, tgt, lemma in seeds:
            Artifact.objects.create(
                user=user,
                deck=deck,
                type=ArtifactType.WORD,
                lemma=lemma,
                source_language=src,
                target_language=tgt,
                data={"meaning": "m", "part_of_speech": "adjective"},
                source=ArtifactSource.MANUAL,
            )

    def test_filter_by_source_language(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?source_language=en")
        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_filter_by_target_language(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?target_language=es")
        assert response.status_code == 200
        assert response.json()["count"] == 4

    def test_combined_source_and_target(self, authed_client, user):
        self._seed(user)
        response = authed_client.get("/api/v1/artifacts?source_language=fr&target_language=es")
        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["lemma"] == "vite"
