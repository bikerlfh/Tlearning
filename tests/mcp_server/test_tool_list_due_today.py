import pytest
from django.utils import timezone

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from mcp_server.auth import set_current_user
from mcp_server.tools import list_due_today
from reviews.enums import FsrsState, ReviewStatus


@pytest.mark.django_db
class TestListDueToday:
    def _seed(self, user, lemma, *, state=FsrsState.NEW, status=ReviewStatus.PENDING, due_offset=0):
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
        rs = a.review_state
        rs.state = state
        rs.status = status
        rs.due_at = timezone.now() + timezone.timedelta(seconds=due_offset)
        if state in (FsrsState.LEARNING, FsrsState.REVIEW, FsrsState.RELEARNING):
            rs.stability = 1.0
        rs.save()
        return a

    def test_returns_due_cards(self, user):
        set_current_user(user)
        self._seed(user, "due_pending")
        self._seed(
            user,
            "due_review",
            state=FsrsState.REVIEW,
            status=ReviewStatus.IN_PROGRESS,
            due_offset=-30,
        )
        result = list_due_today()
        lemmas = [c["lemma"] for c in result]
        assert "due_pending" in lemmas
        assert "due_review" in lemmas

    def test_excludes_learned_and_suspended(self, user):
        set_current_user(user)
        self._seed(user, "due_pending")
        self._seed(user, "done", state=FsrsState.REVIEW, status=ReviewStatus.LEARNED)
        self._seed(user, "off", state=FsrsState.REVIEW, status=ReviewStatus.SUSPENDED)
        result = list_due_today()
        lemmas = [c["lemma"] for c in result]
        assert "done" not in lemmas
        assert "off" not in lemmas

    def test_respects_limit(self, user):
        set_current_user(user)
        for i in range(10):
            self._seed(user, f"card_{i}")
        result = list_due_today(limit=3)
        assert len(result) == 3
