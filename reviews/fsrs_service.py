"""Thin wrapper around the fsrs library.

The rest of the codebase only imports from this module — never directly from `fsrs`.
This isolates the library so we can swap implementations or pin parameters later.

Note: `fsrs` (>=6.x) has no `State.New`. A fresh `Card()` starts in `State.Learning`.
We use our own `FsrsState.NEW` enum value as a marker for "never reviewed", and
materialize a fresh `Card()` when transitioning out of that state.
"""

import datetime as dt

from django.utils import timezone

from .enums import FsrsState, ReviewRating, ReviewStatus
from .models import ReviewLog, ReviewState

# Stability (days) at which a card is considered "learned" for the user-facing status.
LEARNED_THRESHOLD_DAYS = 21.0

_RATING_MAP_TO_FSRS = None  # built lazily to avoid importing fsrs at module load time


def _rating_map():
    global _RATING_MAP_TO_FSRS
    if _RATING_MAP_TO_FSRS is None:
        from fsrs import Rating

        _RATING_MAP_TO_FSRS = {
            ReviewRating.AGAIN: Rating.Again,
            ReviewRating.HARD: Rating.Hard,
            ReviewRating.GOOD: Rating.Good,
            ReviewRating.EASY: Rating.Easy,
        }
    return _RATING_MAP_TO_FSRS


def _to_fsrs_card(rs: ReviewState):
    """Build a fsrs.Card from our ReviewState.

    For NEW (never reviewed), return a fresh Card() — fsrs lib has no New state.
    """
    from fsrs import Card, State

    if rs.state == FsrsState.NEW or rs.stability is None:
        return Card()

    state_lookup = {
        FsrsState.LEARNING: State.Learning,
        FsrsState.REVIEW: State.Review,
        FsrsState.RELEARNING: State.Relearning,
    }
    return Card(
        state=state_lookup[FsrsState(rs.state)],
        due=rs.due_at,
        stability=rs.stability,
        difficulty=rs.difficulty,
        last_review=rs.last_reviewed_at,
    )


_FSRS_STATE_BY_NAME = {
    "Learning": FsrsState.LEARNING,
    "Review": FsrsState.REVIEW,
    "Relearning": FsrsState.RELEARNING,
}


def _from_fsrs_card(card, fallback_now: dt.datetime) -> dict:
    """Extract persistable fields from a fsrs.Card after a review."""
    return {
        "state": _FSRS_STATE_BY_NAME[card.state.name],
        "stability": card.stability,
        "difficulty": card.difficulty,
        "due_at": card.due,
        "last_reviewed_at": card.last_review or fallback_now,
    }


def derive_status(rs: ReviewState) -> ReviewStatus:
    """Compute the user-facing status from FSRS internals.

    Preserves SUSPENDED — never auto-clears that override.
    """
    if rs.status == ReviewStatus.SUSPENDED:
        return ReviewStatus.SUSPENDED
    if rs.state == FsrsState.NEW:
        return ReviewStatus.PENDING
    if rs.state == FsrsState.REVIEW and (rs.stability or 0.0) >= LEARNED_THRESHOLD_DAYS:
        return ReviewStatus.LEARNED
    return ReviewStatus.IN_PROGRESS


def apply_review(
    rs: ReviewState, rating: ReviewRating, *, now: dt.datetime | None = None
) -> ReviewState:
    """Apply a rating to the ReviewState: persist new FSRS fields, append ReviewLog.

    Increments `reps`; increments `lapses` when transitioning out of REVIEW with Again.
    """
    from fsrs import Scheduler

    if now is None:
        now = timezone.now()

    state_before = FsrsState(rs.state)
    scheduler = Scheduler()
    card = _to_fsrs_card(rs)
    new_card, _review_log = scheduler.review_card(card, _rating_map()[ReviewRating(rating)], now)

    # Compute elapsed/scheduled days from card delta
    # (fsrs ReviewLog doesn't expose these directly).
    elapsed_days = 0.0
    if rs.last_reviewed_at is not None:
        elapsed_days = max(0.0, (now - rs.last_reviewed_at).total_seconds() / 86400.0)
    scheduled_days = max(0.0, (new_card.due - now).total_seconds() / 86400.0)

    fields = _from_fsrs_card(new_card, fallback_now=now)
    for k, v in fields.items():
        setattr(rs, k, v)
    rs.reps += 1
    if state_before == FsrsState.REVIEW and ReviewRating(rating) == ReviewRating.AGAIN:
        rs.lapses += 1
    rs.status = derive_status(rs)
    rs.save()

    ReviewLog.objects.create(
        artifact=rs.artifact,
        reviewed_at=now,
        rating=rating,
        elapsed_days=elapsed_days,
        scheduled_days=scheduled_days,
        state_before=state_before,
    )
    return rs
