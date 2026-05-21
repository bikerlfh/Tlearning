from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response

from .enums import FsrsState, ReviewStatus
from .models import ReviewState
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
