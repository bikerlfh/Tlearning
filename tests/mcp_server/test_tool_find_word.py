import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from mcp_server.auth import set_current_user
from mcp_server.tools import find_word


@pytest.mark.django_db
class TestFindWord:
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
            data={"meaning": "heavy, difficult", "part_of_speech": "adjective"},
            source=ArtifactSource.MANUAL,
        )
        Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="bulky",
            source_language="en",
            target_language="es",
            data={"meaning": "large, awkward", "part_of_speech": "adjective"},
            source=ArtifactSource.MANUAL,
        )

    def test_find_matches_lemma(self, user):
        set_current_user(user)
        self._seed(user)
        results = find_word("cumber")
        assert len(results) == 1
        assert results[0]["lemma"] == "cumbersome"

    def test_find_matches_meaning(self, user):
        set_current_user(user)
        self._seed(user)
        results = find_word("difficult")
        assert len(results) == 1
        assert results[0]["lemma"] == "cumbersome"

    def test_find_returns_empty_list_when_no_match(self, user):
        set_current_user(user)
        self._seed(user)
        assert find_word("xyz") == []

    def test_find_respects_limit(self, user):
        set_current_user(user)
        self._seed(user)
        results = find_word("e", limit=1)
        assert len(results) <= 1

    def test_find_isolates_users(self, user, other_user):
        set_current_user(user)
        self._seed(other_user)
        assert find_word("cumber") == []
