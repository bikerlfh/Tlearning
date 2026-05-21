from django.db.models import Count
from rest_framework import viewsets

from api.mixins import UserScopedQuerysetMixin

from .models import Deck
from .serializers import DeckSerializer


class DeckViewSet(UserScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(_artifact_count=Count("artifacts"))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
