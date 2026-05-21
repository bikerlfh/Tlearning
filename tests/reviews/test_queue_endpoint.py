import pytest
from django.utils import timezone

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import FsrsState, ReviewStatus


@pytest.mark.django_db
class TestQueueEndpoint:
    url = "/api/v1/reviews/queue"

    def _make(
        self, user, lemma, *, state=FsrsState.NEW, status=ReviewStatus.PENDING, due_offset_seconds=0
    ):
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
        rs = a.review_state  # signal-created
        rs.state = state
        rs.status = status
        rs.due_at = timezone.now() + timezone.timedelta(seconds=due_offset_seconds)
        if state in (FsrsState.LEARNING, FsrsState.REVIEW, FsrsState.RELEARNING):
            rs.stability = 1.0
        rs.save()
        return a

    def test_queue_excludes_learned_and_suspended(self, authed_client, user):
        self._make(user, "due_pending")
        self._make(user, "done", state=FsrsState.REVIEW, status=ReviewStatus.LEARNED)
        self._make(user, "off", state=FsrsState.REVIEW, status=ReviewStatus.SUSPENDED)
        response = authed_client.get(self.url)
        assert response.status_code == 200
        lemmas = [a["lemma"] for a in response.json()["results"]]
        assert "due_pending" in lemmas
        assert "done" not in lemmas
        assert "off" not in lemmas

    def test_queue_excludes_future_review_cards(self, authed_client, user):
        self._make(
            user,
            "now",
            state=FsrsState.REVIEW,
            status=ReviewStatus.IN_PROGRESS,
            due_offset_seconds=-60,
        )
        self._make(
            user,
            "later",
            state=FsrsState.REVIEW,
            status=ReviewStatus.IN_PROGRESS,
            due_offset_seconds=3600,
        )
        response = authed_client.get(self.url)
        lemmas = [a["lemma"] for a in response.json()["results"]]
        assert "now" in lemmas
        assert "later" not in lemmas

    def test_queue_priority_learning_first_then_review_then_new(self, authed_client, user):
        self._make(user, "new_one")
        self._make(
            user,
            "review_due",
            state=FsrsState.REVIEW,
            status=ReviewStatus.IN_PROGRESS,
            due_offset_seconds=-60,
        )
        self._make(
            user,
            "learning_due",
            state=FsrsState.LEARNING,
            status=ReviewStatus.IN_PROGRESS,
            due_offset_seconds=-30,
        )
        response = authed_client.get(self.url)
        lemmas = [a["lemma"] for a in response.json()["results"]]
        assert lemmas.index("learning_due") < lemmas.index("review_due") < lemmas.index("new_one")

    def test_queue_limit_param(self, authed_client, user):
        for i in range(10):
            self._make(user, f"card_{i}")
        response = authed_client.get(f"{self.url}?limit=3")
        assert len(response.json()["results"]) == 3

    def test_queue_filter_by_deck(self, authed_client, user):
        from decks.models import Deck

        other = Deck.objects.create(user=user, name="o", source_language="en", target_language="es")
        self._make(user, "default_card")
        Artifact.objects.create(
            user=user,
            deck=other,
            type=ArtifactType.WORD,
            lemma="other_card",
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )
        response = authed_client.get(f"{self.url}?deck_id={other.id}")
        lemmas = [c["lemma"] for c in response.json()["results"]]
        assert lemmas == ["other_card"]

    def test_queue_cross_user_isolation(self, authed_client, other_user):
        self._make(other_user, "hidden")
        response = authed_client.get(self.url)
        lemmas = [c["lemma"] for c in response.json()["results"]]
        assert "hidden" not in lemmas
