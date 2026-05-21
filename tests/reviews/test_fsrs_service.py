import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import FsrsState, ReviewRating, ReviewStatus
from reviews.fsrs_service import LEARNED_THRESHOLD_DAYS, apply_review, derive_status
from reviews.models import ReviewLog, ReviewState


@pytest.mark.django_db
class TestApplyReview:
    def _setup(self, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        a = Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="x",
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )
        return a.review_state  # signal-created

    def test_apply_review_good_persists_new_state(self, user):
        rs = self._setup(user)
        original_due = rs.due_at
        apply_review(rs, ReviewRating.GOOD)
        rs.refresh_from_db()
        assert rs.reps == 1
        assert rs.last_reviewed_at is not None
        assert rs.due_at > original_due
        assert rs.stability is not None
        assert rs.difficulty is not None
        assert rs.state in (FsrsState.LEARNING, FsrsState.REVIEW)

    def test_apply_review_writes_review_log(self, user):
        rs = self._setup(user)
        apply_review(rs, ReviewRating.HARD)
        log = ReviewLog.objects.filter(artifact=rs.artifact).first()
        assert log is not None
        assert log.rating == ReviewRating.HARD

    def test_apply_review_increments_reps(self, user):
        rs = self._setup(user)
        apply_review(rs, ReviewRating.GOOD)
        apply_review(rs, ReviewRating.GOOD)
        rs.refresh_from_db()
        assert rs.reps == 2

    def test_apply_review_logs_two_entries_after_two_reviews(self, user):
        rs = self._setup(user)
        apply_review(rs, ReviewRating.GOOD)
        apply_review(rs, ReviewRating.AGAIN)
        assert ReviewLog.objects.filter(artifact=rs.artifact).count() == 2


class TestDeriveStatus:
    def test_new_state_is_pending(self):
        rs = ReviewState(state=FsrsState.NEW, stability=None, status=ReviewStatus.PENDING)
        assert derive_status(rs) == ReviewStatus.PENDING

    def test_learning_state_is_in_progress(self):
        rs = ReviewState(state=FsrsState.LEARNING, stability=2.0, status=ReviewStatus.PENDING)
        assert derive_status(rs) == ReviewStatus.IN_PROGRESS

    def test_review_high_stability_is_learned(self):
        rs = ReviewState(
            state=FsrsState.REVIEW,
            stability=LEARNED_THRESHOLD_DAYS,
            status=ReviewStatus.IN_PROGRESS,
        )
        assert derive_status(rs) == ReviewStatus.LEARNED

    def test_review_low_stability_is_in_progress(self):
        rs = ReviewState(state=FsrsState.REVIEW, stability=5.0, status=ReviewStatus.IN_PROGRESS)
        assert derive_status(rs) == ReviewStatus.IN_PROGRESS

    def test_relearning_is_in_progress(self):
        rs = ReviewState(
            state=FsrsState.RELEARNING, stability=10.0, status=ReviewStatus.IN_PROGRESS
        )
        assert derive_status(rs) == ReviewStatus.IN_PROGRESS

    def test_suspended_status_preserved(self):
        """If status is already SUSPENDED, derive_status must NOT auto-revert it."""
        rs = ReviewState(
            state=FsrsState.REVIEW,
            stability=LEARNED_THRESHOLD_DAYS,
            status=ReviewStatus.SUSPENDED,
        )
        assert derive_status(rs) == ReviewStatus.SUSPENDED
