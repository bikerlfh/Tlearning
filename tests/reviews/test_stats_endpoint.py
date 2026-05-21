from datetime import timedelta

import pytest
from django.utils import timezone

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from reviews.enums import FsrsState, ReviewRating, ReviewStatus
from reviews.models import ReviewLog


def _make_artifact(user, lemma, *, type_=ArtifactType.WORD, status=ReviewStatus.PENDING):
    from decks.models import Deck

    deck = Deck.objects.filter(user=user, is_default=True).first()
    a = Artifact.objects.create(
        user=user,
        deck=deck,
        type=type_,
        lemma=lemma,
        source_language="en",
        target_language="es",
        data={"meaning": "m", "part_of_speech": "noun"},
        source=ArtifactSource.MANUAL,
    )
    rs = a.review_state
    rs.status = status
    rs.state = FsrsState.NEW
    rs.due_at = timezone.now()
    rs.save()
    return a


def _log(artifact, *, days_ago=0, rating=ReviewRating.GOOD, state_before=FsrsState.NEW):
    return ReviewLog.objects.create(
        artifact=artifact,
        reviewed_at=timezone.now() - timedelta(days=days_ago),
        rating=rating,
        elapsed_days=0.0,
        scheduled_days=1.0,
        state_before=state_before,
    )


@pytest.mark.django_db
class TestStatsEndpoint:
    url = "/api/v1/reviews/stats"

    def test_requires_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code in (401, 403)

    def test_empty_user_returns_zeros_and_full_heatmap(self, authed_client):
        response = authed_client.get(self.url)
        assert response.status_code == 200
        data = response.json()
        assert data["due_today"] == 0
        assert data["studied_today"] == 0
        assert data["streak_days"] == 0
        assert len(data["heatmap"]) == 90
        assert all(cell["reviews"] == 0 for cell in data["heatmap"])
        assert data["retention_curve"] == []
        assert data["total_learned"] == 0

    def test_counts_due_today_from_active_states(self, authed_client, user):
        _make_artifact(user, "due1", status=ReviewStatus.PENDING)
        _make_artifact(user, "due2", status=ReviewStatus.PENDING)
        _make_artifact(user, "done", status=ReviewStatus.LEARNED)
        response = authed_client.get(self.url)
        data = response.json()
        assert data["due_today"] == 2

    def test_studied_today_counts_only_logs_from_today(self, authed_client, user):
        a = _make_artifact(user, "x")
        _log(a, days_ago=0)
        _log(a, days_ago=0)
        _log(a, days_ago=1)  # yesterday — should not count
        response = authed_client.get(self.url)
        assert response.json()["studied_today"] == 2

    def test_streak_counts_contiguous_days_with_reviews(self, authed_client, user):
        a = _make_artifact(user, "x")
        for d in range(5):
            _log(a, days_ago=d)
        # Skip day 5, day 6 has a review (breaks streak at 5)
        _log(a, days_ago=6)
        response = authed_client.get(self.url)
        assert response.json()["streak_days"] == 5

    def test_streak_zero_when_no_review_today(self, authed_client, user):
        a = _make_artifact(user, "x")
        _log(a, days_ago=1)
        _log(a, days_ago=2)
        response = authed_client.get(self.url)
        assert response.json()["streak_days"] == 0

    def test_retention_curve_buckets_by_review_number(self, authed_client, user):
        a = _make_artifact(user, "x")
        b = _make_artifact(user, "y")
        # First reviews: 1 success, 1 fail
        _log(a, days_ago=5, rating=ReviewRating.GOOD)
        _log(b, days_ago=5, rating=ReviewRating.AGAIN)
        # Second reviews: both success
        _log(a, days_ago=4, rating=ReviewRating.GOOD)
        _log(b, days_ago=4, rating=ReviewRating.GOOD)
        response = authed_client.get(self.url)
        curve = {row["review_number"]: row for row in response.json()["retention_curve"]}
        assert curve[1]["samples"] == 2
        assert curve[1]["rate"] == 0.5
        assert curve[2]["samples"] == 2
        assert curve[2]["rate"] == 1.0

    def test_distributions_reflect_library(self, authed_client, user):
        _make_artifact(user, "w1", type_=ArtifactType.WORD)
        _make_artifact(user, "w2", type_=ArtifactType.WORD)
        _make_artifact(user, "i1", type_=ArtifactType.IDIOM, status=ReviewStatus.LEARNED)
        response = authed_client.get(self.url)
        data = response.json()
        assert data["type_distribution"].get("word") == 2
        assert data["type_distribution"].get("idiom") == 1
        assert data["status_distribution"].get("pending") == 2
        assert data["status_distribution"].get("learned") == 1
        assert data["total_learned"] == 1

    def test_does_not_leak_other_users_data(self, authed_client, other_user):
        _make_artifact(other_user, "leak", status=ReviewStatus.LEARNED)
        response = authed_client.get(self.url)
        data = response.json()
        assert data["due_today"] == 0
        assert data["total_learned"] == 0
        assert data["type_distribution"] == {}
