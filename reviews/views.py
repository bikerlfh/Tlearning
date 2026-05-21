from collections import defaultdict
from datetime import timedelta

from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.utils import timezone
from rest_framework import generics
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import APIView

from artifacts.models import Artifact

from .enums import FsrsState, ReviewRating, ReviewStatus
from .fsrs_service import apply_review
from .models import ReviewLog, ReviewState
from .serializers import QueueCardSerializer


def _due_queue(user, deck_id=None):
    """Build the eligible review queue for a user: excludes learned/suspended,
    requires due_at <= now for non-NEW cards, orders by priority."""
    now = timezone.now()
    qs = (
        ReviewState.objects.select_related("artifact", "artifact__deck")
        .filter(
            artifact__user=user,
        )
        .exclude(
            status__in=[ReviewStatus.LEARNED, ReviewStatus.SUSPENDED],
        )
        .filter(
            Q(state=FsrsState.NEW) | Q(due_at__lte=now),
        )
    )
    if deck_id:
        qs = qs.filter(artifact__deck_id=deck_id)
    priority = Case(
        When(state__in=[FsrsState.LEARNING, FsrsState.RELEARNING], then=Value(1)),
        When(state=FsrsState.REVIEW, then=Value(2)),
        When(state=FsrsState.NEW, then=Value(3)),
        default=Value(99),
        output_field=IntegerField(),
    )
    return qs.annotate(_priority=priority).order_by("_priority", "due_at", "artifact__created_at")


class QueueView(generics.GenericAPIView):
    serializer_class = QueueCardSerializer

    def get(self, request):
        qs = _due_queue(request.user, deck_id=request.query_params.get("deck_id"))
        try:
            limit = int(request.query_params.get("limit", 20))
        except ValueError:
            limit = 20
        items = list(qs[:limit])
        serializer = self.get_serializer(items, many=True, context={"request": request})
        return Response({"results": serializer.data, "count": len(serializer.data)})


class AnswerView(APIView):
    def post(self, request, artifact_id):
        try:
            artifact = Artifact.objects.select_related("review_state").get(
                id=artifact_id, user=request.user
            )
        except Artifact.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        try:
            rating = ReviewRating(int(request.data.get("rating", 0)))
        except (ValueError, TypeError):
            return Response(
                {"rating": ["Must be one of 1/2/3/4."]},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        rs = artifact.review_state
        apply_review(rs, rating)

        next_card = _due_queue(request.user).exclude(artifact=artifact).first()
        next_serialized = (
            QueueCardSerializer(next_card, context={"request": request}).data
            if next_card is not None
            else None
        )
        return Response(
            {
                "review_state": {
                    "state": rs.state,
                    "status": rs.status,
                    "due_at": rs.due_at,
                    "reps": rs.reps,
                    "lapses": rs.lapses,
                },
                "next_card": next_serialized,
            },
            status=http_status.HTTP_200_OK,
        )


class StatsView(APIView):
    """Aggregated review metrics for the current user: due/studied today, streak,
    90-day heatmap, retention curve (success rate vs reviews-so-far), and
    type/status distributions across the library."""

    def get(self, request):
        user = request.user
        now = timezone.now()
        today = timezone.localdate()
        ninety_days_ago = today - timedelta(days=89)

        due_today = _due_queue(user).count()

        logs = ReviewLog.objects.filter(artifact__user=user)
        today_start = (
            timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
            if timezone.is_naive(now)
            else now.replace(hour=0, minute=0, second=0, microsecond=0)
        )
        studied_today = logs.filter(reviewed_at__gte=today_start).count()

        # Heatmap: count reviews per local date for the last 90 days
        recent = logs.filter(reviewed_at__date__gte=ninety_days_ago).values_list(
            "reviewed_at",
            flat=True,
        )
        by_day: dict[str, int] = defaultdict(int)
        for ts in recent:
            by_day[ts.date().isoformat()] += 1
        heatmap = []
        for offset in range(90):
            d = ninety_days_ago + timedelta(days=offset)
            heatmap.append({"date": d.isoformat(), "reviews": by_day.get(d.isoformat(), 0)})

        # Streak: count consecutive days ending today with at least one review.
        streak_days = 0
        cursor = today
        while True:
            if by_day.get(cursor.isoformat(), 0) > 0:
                streak_days += 1
                cursor -= timedelta(days=1)
            else:
                break

        # Retention curve: bucket each log by (reps_so_far for that artifact at the
        # time of review). Rating >= 3 counts as "successful recall".
        # We approximate reps_so_far via row_number per artifact ordered by reviewed_at.
        per_artifact_seen: dict = defaultdict(int)
        bucket_total: dict[int, int] = defaultdict(int)
        bucket_success: dict[int, int] = defaultdict(int)
        for row in logs.order_by("reviewed_at").values("artifact_id", "rating"):
            per_artifact_seen[row["artifact_id"]] += 1
            n = per_artifact_seen[row["artifact_id"]]
            if n > 30:
                continue
            bucket_total[n] += 1
            if row["rating"] >= 3:
                bucket_success[n] += 1
        retention_curve = [
            {
                "review_number": n,
                "rate": (bucket_success[n] / bucket_total[n]) if bucket_total[n] else 0.0,
                "samples": bucket_total[n],
            }
            for n in range(1, 31)
            if bucket_total[n]
        ]

        # Distributions
        type_counts = (
            Artifact.objects.filter(user=user).values("type").annotate(c=Count("id")).order_by("-c")
        )
        type_distribution = {row["type"]: row["c"] for row in type_counts}

        status_counts = (
            ReviewState.objects.filter(artifact__user=user)
            .values("status")
            .annotate(c=Count("id"))
            .order_by("-c")
        )
        status_distribution = {row["status"]: row["c"] for row in status_counts}

        return Response(
            {
                "due_today": due_today,
                "studied_today": studied_today,
                "streak_days": streak_days,
                "heatmap": heatmap,
                "retention_curve": retention_curve,
                "type_distribution": type_distribution,
                "status_distribution": status_distribution,
                "total_learned": status_distribution.get(ReviewStatus.LEARNED, 0),
            }
        )
