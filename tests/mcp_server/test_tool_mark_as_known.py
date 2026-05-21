import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from mcp_server.auth import set_current_user
from mcp_server.tools import mark_as_known
from reviews.enums import ReviewStatus


@pytest.mark.django_db
class TestMarkAsKnown:
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

    def test_mark_as_known_sets_learned(self, user):
        set_current_user(user)
        a = self._make(user, "x")
        result = mark_as_known("x")
        assert result["status"] == "learned"
        a.refresh_from_db()
        assert a.review_state.status == ReviewStatus.LEARNED

    def test_lemma_not_found_returns_none_status(self, user):
        set_current_user(user)
        result = mark_as_known("nonexistent")
        assert result["status"] is None
        assert "not found" in result["message"].lower()

    def test_isolates_users(self, user, other_user):
        set_current_user(user)
        self._make(other_user, "hidden")
        result = mark_as_known("hidden")
        assert result["status"] is None
