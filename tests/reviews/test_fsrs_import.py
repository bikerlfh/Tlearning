"""Smoke tests confirming fsrs is importable and the basic API matches our assumptions."""


def test_fsrs_basic_review_cycle():
    """Verify Scheduler, Card, Rating exist and review_card returns (new_card, log)."""
    import datetime as dt

    from fsrs import Card, Rating, Scheduler

    scheduler = Scheduler()
    card = Card()
    assert card.state is not None

    now = dt.datetime.now(dt.UTC)
    new_card, review_log = scheduler.review_card(card, Rating.Good, now)
    assert new_card.state is not None
    assert new_card.due > now
    assert review_log.rating == Rating.Good


def test_fsrs_rating_enum_values():
    from fsrs import Rating

    assert int(Rating.Again) == 1
    assert int(Rating.Hard) == 2
    assert int(Rating.Good) == 3
    assert int(Rating.Easy) == 4


def test_fsrs_state_enum_values():
    """Document the actual State enum members (no `New` state in fsrs 6.x)."""
    from fsrs import State

    assert {member.name for member in State} == {"Learning", "Review", "Relearning"}
