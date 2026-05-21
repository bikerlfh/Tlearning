import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact


@pytest.mark.django_db
class TestArtifactListFilters:
    def _bulk(self, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        for lemma in ["cumbersome", "ubiquitous", "frequent", "rare"]:
            Artifact.objects.create(
                user=user,
                deck=deck,
                type=ArtifactType.WORD,
                lemma=lemma,
                source_language="en",
                target_language="es",
                data={"meaning": f"def of {lemma}", "part_of_speech": "adjective"},
                source=ArtifactSource.MANUAL,
            )

    def test_list_returns_all_for_user(self, authed_client, user):
        self._bulk(user)
        response = authed_client.get("/api/v1/artifacts")
        assert response.status_code == 200
        assert response.json()["count"] == 4

    def test_filter_by_type(self, authed_client, user):
        self._bulk(user)
        response = authed_client.get("/api/v1/artifacts?type=word")
        assert response.status_code == 200
        assert response.json()["count"] == 4

    def test_search_q_matches_lemma(self, authed_client, user):
        self._bulk(user)
        response = authed_client.get("/api/v1/artifacts?q=cumbersome")
        assert response.status_code == 200
        lemmas = [a["lemma"] for a in response.json()["results"]]
        assert lemmas == ["cumbersome"]

    def test_filter_by_deck_id(self, authed_client, user):
        from decks.models import Deck

        self._bulk(user)
        other_deck = Deck.objects.create(
            user=user, name="o", source_language="en", target_language="es"
        )
        Artifact.objects.create(
            user=user,
            deck=other_deck,
            type=ArtifactType.WORD,
            lemma="only-here",
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )
        response = authed_client.get(f"/api/v1/artifacts?deck_id={other_deck.id}")
        assert response.json()["count"] == 1
